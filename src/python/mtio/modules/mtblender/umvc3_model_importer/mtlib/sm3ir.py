import struct
import numpy as np
from .sm3 import regtype, TEXTYPE

OP = dict(nop=0, mov=1, add=2, sub=3, mad=4, mul=5, rcp=6, rsq=7, dp3=8, dp4=9, min=10, max=11, slt=12,
          sge=13, exp=14, log=15, lit=16, dst=17, lrp=18, frc=19, abs=35, nrm=36, sincos=37, rep=38,
          endrep=39, if_=40, ifc=41, else_=42, endif=43, break_=44, breakc=45, mova=46, texkill=65,
          texld=66, cmp=88, dp2add=90, pow=32, dcl=31, def_=81, defb=47, defi=48, setp=94, texldl=95)
INV = {v: k for k, v in OP.items()}


class Graph:
    def __init__(self):
        self.nodes = []
        self.index = {}

    def add(self, node):
        i = self.index.get(node)
        if i is None:
            i = len(self.nodes)
            self.nodes.append(node)
            self.index[node] = i
        return i

    def k(self, v):
        return self.add(('k', float(np.float32(v))))

    def kval(self, i):
        n = self.nodes[i]
        return n[1] if n[0] == 'k' else None

    # light constant folding, keeps the node count down without changing results
    def op(self, name, *args):
        ks = [self.kval(a) for a in args]
        if all(x is not None for x in ks):
            return self.k(_eval_scalar(name, *[np.float32(x) for x in ks]))
        if name == 'mul':
            a, b = args
            if ks[0] == 1.0: return b
            if ks[1] == 1.0: return a
            if ks[0] == 0.0 or ks[1] == 0.0: return self.k(0.0)   # shader math has no NaN inputs here
            if ks[0] == -1.0: return self.op('neg', b)
            if ks[1] == -1.0: return self.op('neg', a)
        if name == 'add':
            a, b = args
            if ks[0] == 0.0: return b
            if ks[1] == 0.0: return a
        if name == 'neg' and self.nodes[args[0]][:2] == ('op', 'neg'):
            return self.nodes[args[0]][2]
        if name in ('add', 'mul', 'max', 'min') and args[0] > args[1]:
            args = (args[1], args[0])
        return self.add(('op', name) + tuple(args))


def _eval_scalar(name, *a):
    with np.errstate(all='ignore'):
        return float(EVAL[name](*[np.asarray(x, dtype=np.float32) for x in a]))


def _rcp(x):
    return np.float32(1.0) / x

EVAL = {
    'add': lambda a, b: a + b,
    'mul': lambda a, b: a * b,
    'max': np.maximum,
    'min': np.minimum,
    'neg': lambda a: -a,
    'abs': np.abs,
    'rcp': _rcp,
    'rsq': lambda a: _rcp(np.sqrt(np.abs(a))),
    'exp2': np.exp2,
    'log2': lambda a: np.log2(np.abs(a)),
    'frc': lambda a: a - np.floor(a),
    'sel': lambda a, b, c: np.where(a >= 0, b, c),
    'lt': lambda a, b: (a < b).astype(np.float32),
    'ge': lambda a, b: (a >= b).astype(np.float32),
    'gt': lambda a, b: (a > b).astype(np.float32),
    'le': lambda a, b: (a <= b).astype(np.float32),
    'eq': lambda a, b: (a == b).astype(np.float32),
    'ne': lambda a, b: (a != b).astype(np.float32),
    'pow': lambda a, b: np.exp2(b * np.log2(np.abs(a))),
    'sqrt': lambda a: np.sqrt(a),
    'mix': lambda t, a, b: np.where(t > 0.5, b, a),     # branch select, t is 0/1
}


class Builder:
    def __init__(self, sh, ints=None, bools=None):
        self.sh = sh
        self.g = Graph()
        self.r = {}            # (bank, reg) -> [4 node ids]
        self.defs = {}         # c reg -> 4 floats
        self.idefs = {}
        self.ints = {k: tuple(v) for k, v in (ints or {}).items()}
        self.bools = bools or {}
        self.kill = None
        self.texs = []
        for t, a in sh.insts:
            op = t & 0xffff
            if op == OP['def_']:
                self.defs[a[0] & 0x7ff] = struct.unpack('<4f', struct.pack('<4I', *a[1:5]))
            elif op == OP['defi']:
                self.idefs[a[0] & 0x7ff] = struct.unpack('<4i', struct.pack('<4I', *a[1:5]))
        self.samplers = {}
        for t, a in sh.insts:
            if t & 0xffff == OP['dcl'] and regtype(a[1]) == 10:
                self.samplers[a[1] & 0x7ff] = TEXTYPE.get((a[0] >> 27) & 0xf, '2d')

    # -- registers
    def read_reg(self, t):
        g = self.g
        rt = regtype(t); num = t & 0x7ff
        if t & 0x2000:
            raise NotImplementedError('relative addressing')
        if rt == 0:      # temp
            return self.r.get(('r', num), [g.k(0)] * 4)
        if rt == 2:      # const float
            if num in self.defs:
                return [g.k(x) for x in self.defs[num]]
            return [g.add(('c', num, k)) for k in range(4)]
        if rt == 1:      # input
            return [g.add(('v', num, k)) for k in range(4)]
        if rt == 17:     # misc: vPos / vFace
            if num == 1:
                f = g.add(('vface',))
                return [f] * 4
            return [g.add(('vpos', k)) for k in range(4)]
        if rt == 7:      # int const
            v = self.idefs.get(num) or self.ints.get(num) or (0, 0, 0, 0)
            return [g.k(x) for x in v]
        if rt == 14:     # bool const
            return [g.k(1.0 if self.bools.get(num) else 0.0)] * 4
        if rt == 8:      # output read back (oC)
            return self.r.get(('o', num), [g.k(0)] * 4)
        raise NotImplementedError(f'read reg type {rt}')

    def src(self, t):
        g = self.g
        v = self.read_reg(t)
        sw = (t >> 16) & 0xff
        v = [v[(sw >> (2 * k)) & 3] for k in range(4)]
        mod = (t >> 24) & 0xf
        if mod == 0:
            return v
        if mod == 1:
            return [g.op('neg', x) for x in v]
        if mod == 11:
            return [g.op('abs', x) for x in v]
        if mod == 12:
            return [g.op('neg', g.op('abs', x)) for x in v]
        if mod == 6:
            return [g.op('add', g.k(1.0), g.op('neg', x)) for x in v]
        if mod == 4:   # bx2
            return [g.op('add', g.op('mul', x, g.k(2.0)), g.k(-1.0)) for x in v]
        if mod == 5:
            return [g.op('neg', g.op('add', g.op('mul', x, g.k(2.0)), g.k(-1.0))) for x in v]
        if mod == 7:
            return [g.op('mul', x, g.k(2.0)) for x in v]
        raise NotImplementedError(f'src modifier {mod}')

    def write(self, t, vals, mask_override=None):
        g = self.g
        rt = regtype(t); num = t & 0x7ff
        bank = {0: 'r', 8: 'o', 6: 'vo'}.get(rt)
        if bank is None:
            raise NotImplementedError(f'write reg type {rt}')
        m = (t >> 16) & 0xf if mask_override is None else mask_override
        sat = (t >> 20) & 1
        cur = list(self.r.get((bank, num), [g.k(0)] * 4))
        for k in range(4):
            if m & (1 << k):
                x = vals[k]
                if sat:
                    x = g.op('min', g.op('max', x, g.k(0.0)), g.k(1.0))
                cur[k] = x
        self.r[(bank, num)] = cur

    # -- ops
    def dot(self, a, b, n):
        g = self.g
        s = g.op('mul', a[0], b[0])
        for k in range(1, n):
            s = g.op('add', s, g.op('mul', a[k], b[k]))
        return s

    def run(self):
        insts = [(t, a) for t, a in self.sh.insts if t & 0xffff not in (OP['dcl'], OP['def_'], OP['defi'], OP['defb'])]
        self._block(insts, 0, len(insts))
        return self

    def _match(self, insts, i, open_ops, close_op, else_op=None):
        depth = 0; els = None
        for j in range(i + 1, len(insts)):
            op = insts[j][0] & 0xffff
            if op in open_ops:
                depth += 1
            elif op == close_op:
                if depth == 0:
                    return j, els
                depth -= 1
            elif else_op is not None and op == else_op and depth == 0:
                els = j
        raise ValueError('unbalanced block')

    def _block(self, insts, i, end):
        g = self.g
        while i < end:
            t, a = insts[i]
            op = t & 0xffff
            name = INV.get(op)
            if name in ('ifc', 'if_'):
                j, els = self._match(insts, i, (OP['if_'], OP['ifc']), OP['endif'], OP['else_'])
                if name == 'ifc':
                    ctl = (t >> 16) & 7
                    x = self.src(a[0])[0]; y = self.src(a[1])[0]
                    cmp = {1: 'gt', 2: 'eq', 3: 'ge', 4: 'lt', 5: 'ne', 6: 'le'}[ctl]
                    cond = g.op(cmp, x, y)
                else:
                    cond = self.src(a[0])[0]
                saved = dict(self.r); saved_kill = self.kill
                self._block(insts, i + 1, els if els is not None else j)
                then_r, then_kill = self.r, self.kill
                self.r = dict(saved); self.kill = saved_kill
                if els is not None:
                    self._block(insts, els + 1, j)
                else_r, else_kill = self.r, self.kill
                merged = {}
                for key in set(then_r) | set(else_r):
                    tv = then_r.get(key, [g.k(0)] * 4); ev = else_r.get(key, [g.k(0)] * 4)
                    merged[key] = [tv[k] if tv[k] == ev[k] else g.op('mix', cond, ev[k], tv[k]) for k in range(4)]
                self.r = merged
                if then_kill != else_kill:
                    zero = g.k(-1.0)
                    self.kill = g.op('mix', cond, else_kill if else_kill is not None else zero,
                                     then_kill if then_kill is not None else zero)
                i = j + 1
                continue
            if name == 'rep':
                j, _ = self._match(insts, i, (OP['rep'],), OP['endrep'])
                count = int(round(g.kval(self.src(a[0])[0]) or 0))
                for _ in range(max(count, 0)):
                    self._block(insts, i + 1, j)
                i = j + 1
                continue
            self.inst(t, a)
            i += 1

    def inst(self, t, a):
        g = self.g
        op = t & 0xffff
        name = INV.get(op)
        if name == 'nop':
            return
        if name == 'texkill':
            v = self.read_reg(a[0])
            sw = (a[0] >> 16) & 0xff
            m = (a[0] >> 16) & 0xf   # texkill uses the dst style mask
            comps = [v[k] for k in range(4) if m & (1 << k)] or v[:3]
            # killed when any component < 0: kill value = -min(comps) > 0
            mn = comps[0]
            for c in comps[1:]:
                mn = g.op('min', mn, c)
            kv = g.op('neg', mn)
            self.kill = kv if self.kill is None else g.op('max', self.kill, kv)
            return
        d = a[0]
        if name in ('texld', 'texldl'):
            coord = self.src(a[1])
            s = a[2] & 0x7ff
            kind = self.samplers.get(s, '2d')
            tn = g.add(('tex', s, kind, tuple(coord)))
            self.texs.append(tn)
            vals = [g.add(('texc', tn, k)) for k in range(4)]
            sw = (a[2] >> 16) & 0xff
            vals = [vals[(sw >> (2 * k)) & 3] for k in range(4)]
            self.write(d, vals)
            return
        S = [self.src(x) for x in a[1:]]
        if name == 'mov': v = S[0]
        elif name == 'add': v = [g.op('add', S[0][k], S[1][k]) for k in range(4)]
        elif name == 'sub': v = [g.op('add', S[0][k], g.op('neg', S[1][k])) for k in range(4)]
        elif name == 'mul': v = [g.op('mul', S[0][k], S[1][k]) for k in range(4)]
        elif name == 'mad': v = [g.op('add', g.op('mul', S[0][k], S[1][k]), S[2][k]) for k in range(4)]
        elif name == 'min': v = [g.op('min', S[0][k], S[1][k]) for k in range(4)]
        elif name == 'max': v = [g.op('max', S[0][k], S[1][k]) for k in range(4)]
        elif name == 'rcp': v = [g.op('rcp', S[0][0])] * 4
        elif name == 'rsq': v = [g.op('rsq', S[0][0])] * 4
        elif name == 'exp': v = [g.op('exp2', S[0][0])] * 4
        elif name == 'log': v = [g.op('log2', S[0][0])] * 4
        elif name == 'pow': v = [g.op('pow', S[0][0], S[1][0])] * 4
        elif name == 'frc': v = [g.op('frc', S[0][k]) for k in range(4)]
        elif name == 'abs': v = [g.op('abs', S[0][k]) for k in range(4)]
        elif name == 'dp3': v = [self.dot(S[0], S[1], 3)] * 4
        elif name == 'dp4': v = [self.dot(S[0], S[1], 4)] * 4
        elif name == 'dp2add': v = [g.op('add', self.dot(S[0], S[1], 2), S[2][0])] * 4
        elif name == 'cmp': v = [g.op('sel', S[0][k], S[1][k], S[2][k]) for k in range(4)]
        elif name == 'slt': v = [g.op('lt', S[0][k], S[1][k]) for k in range(4)]
        elif name == 'sge': v = [g.op('ge', S[0][k], S[1][k]) for k in range(4)]
        elif name == 'lrp':
            v = [g.op('add', g.op('mul', S[0][k], g.op('add', S[1][k], g.op('neg', S[2][k]))), S[2][k]) for k in range(4)]
        elif name == 'nrm':
            l = g.op('rsq', self.dot(S[0], S[0], 3))
            v = [g.op('mul', S[0][k], l) for k in range(3)] + [g.op('mul', S[0][3], l)]
        else:
            raise NotImplementedError(f'opcode {name or op}')
        self.write(d, v)

    @property
    def outputs(self):
        out = {f'oC{k[1]}': v for k, v in self.r.items() if k[0] == 'o'}
        out.update({f'o{k[1]}': v for k, v in self.r.items() if k[0] == 'vo'})
        return out


def build(sh, ints=None, bools=None):
    return Builder(sh, ints, bools).run()

def evaluate(b, consts, inputs, samplers, vface=1.0, vpos=None, n=1):
    g = b.g
    want = set()
    stack = [x for v in b.outputs.values() for x in v] + ([b.kill] if b.kill is not None else [])
    while stack:
        i = stack.pop()
        if i in want: continue
        want.add(i)
        node = g.nodes[i]
        if node[0] == 'op': stack.extend(node[2:])
        elif node[0] == 'tex': stack.extend(node[3])
        elif node[0] == 'texc': stack.append(node[1])
    val = {}
    tex_cache = {}
    with np.errstate(all='ignore'):
        for i in sorted(want):
            node = g.nodes[i]
            kind = node[0]
            if kind == 'k':
                val[i] = np.full(n, node[1], np.float32)
            elif kind == 'c':
                c = np.asarray(consts.get(node[1], (0, 0, 0, 0)), np.float32)
                val[i] = (c[..., node[2]] * np.ones(n, np.float32)).astype(np.float32)
            elif kind == 'v':
                val[i] = np.asarray(inputs[node[1]], np.float32)[:, node[2]]
            elif kind == 'vface':
                val[i] = np.full(n, vface, np.float32)
            elif kind == 'vpos':
                val[i] = np.asarray(vpos, np.float32)[:, node[1]]
            elif kind == 'op':
                val[i] = EVAL[node[1]](*[val[x] for x in node[2:]]).astype(np.float32)
            elif kind == 'tex':
                coord = np.stack([val[x] for x in node[3]], 1)
                fn = samplers.get(node[1])
                tex_cache[i] = fn(coord) if fn else np.zeros((n, 4), np.float32)
            elif kind == 'texc':
                val[i] = np.asarray(tex_cache[node[1]], np.float32)[:, node[2]]
    out = {k: np.stack([val[x] for x in v], 1) for k, v in b.outputs.items()}
    kill = val[b.kill] if b.kill is not None else None
    return out, kill
