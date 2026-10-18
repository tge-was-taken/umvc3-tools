"""Minimal D3D9 SM2/SM3 bytecode disassembler with CTAB constant naming."""
import struct

OPS = {0:'nop',1:'mov',2:'add',3:'sub',4:'mad',5:'mul',6:'rcp',7:'rsq',8:'dp3',9:'dp4',10:'min',11:'max',
12:'slt',13:'sge',14:'exp',15:'log',16:'lit',17:'dst',18:'lrp',19:'frc',20:'m4x4',21:'m4x3',22:'m3x4',
23:'m3x3',24:'m3x2',25:'call',26:'callnz',27:'loop',28:'ret',29:'endloop',30:'label',31:'dcl',32:'pow',
33:'crs',34:'sgn',35:'abs',36:'nrm',37:'sincos',38:'rep',39:'endrep',40:'if',41:'ifc',42:'else',43:'endif',
44:'break',45:'breakc',46:'mova',47:'defb',48:'defi',64:'texcoord',65:'texkill',66:'texld',67:'texbem',
68:'texbeml',78:'expp',79:'logp',80:'cnd',81:'def',88:'cmp',89:'bem',90:'dp2add',91:'dsx',92:'dsy',
93:'texldd',94:'setp',95:'texldl',96:'breakp'}
NOOPERANDS = {0,28,29,39,42,43,44}
REG = {0:'r',1:'v',2:'c',3:'a',4:'oPos',5:'oD',6:'o',7:'i',8:'oC',9:'oDepth',10:'s',11:'c',12:'c',13:'c',
14:'b',15:'aL',16:'half',17:'misc',18:'l',19:'p'}
CMP = {1:'_gt',2:'_eq',3:'_ge',4:'_lt',5:'_ne',6:'_le'}
USAGE = {0:'position',1:'blendweight',2:'blendindices',3:'normal',4:'psize',5:'texcoord',6:'tangent',
7:'binormal',8:'tessfactor',9:'positiont',10:'color',11:'fog',12:'depth',13:'sample'}
TEXTYPE = {2:'2d',3:'cube',4:'volume'}

def parse_ctab(words, start, n):
    raw = struct.pack('<%dI' % n, *words[start:start+n])
    if raw[:4] != b'CTAB':
        return None
    d = raw[4:]
    size, creator, ver, count, cinfo, flags, target = struct.unpack_from('<7I', d, 0)
    def cstr(o):
        e = d.index(b'\0', o); return d[o:e].decode('latin1')
    out = []
    for k in range(count):
        name, rset, ridx, rcnt, _, tinfo, dflt = struct.unpack_from('<IHHHHII', d, cinfo + 20*k)
        defv = None
        if dflt and rset == 2:
            defv = struct.unpack_from('<%df' % (rcnt*4), d, dflt)
        out.append(dict(name=cstr(name), set=rset, idx=ridx, cnt=rcnt, default=defv))
    return dict(target=cstr(target), creator=cstr(creator), consts=out)

def regtype(t):
    return ((t >> 28) & 7) | ((t >> 8) & 0x18)

class Shader:
    def __init__(self, words, base=0):
        self.words = words
        self.ver = words[0]
        self.ps = (self.ver >> 16) == 0xFFFF
        self.major = (self.ver >> 8) & 0xff
        self.ctab = None
        self.length = None
        self.insts = []
        self.defs = {}
        self._parse()
        self.names = {}
        if self.ctab:
            for c in self.ctab['consts']:
                pre = {0:'b',1:'i',2:'c',3:'s'}[c['set']]
                for j in range(c['cnt']):
                    self.names[(pre, c['idx']+j)] = c['name'] + (f'[{j}]' if c['cnt'] > 1 else '')

    def _parse(self):
        w = self.words; i = 1
        while i < len(w):
            t = w[i]
            op = t & 0xffff
            if op == 0xFFFF:
                self.length = i + 1; return
            if op == 0xFFFE:
                n = (t >> 16) & 0x7fff
                if self.ctab is None:
                    self.ctab = parse_ctab(w, i+1, n)
                i += 1 + n; continue
            n = (t >> 24) & 0xf
            self.insts.append((t, w[i+1:i+1+n]))
            i += 1 + n
        raise ValueError('no end token')

    def reg(self, t, src=True, rel=None):
        rt = regtype(t); num = t & 0x7ff
        if rt == 17:
            s = {0:'vPos',1:'vFace'}.get(num, f'misc{num}')
        elif rt in (4,):
            s = {0:'oPos',1:'oFog',2:'oPts'}.get(num)
        elif rt == 3:
            s = (f't{num}' if self.ps else f'a{num}')
        elif rt == 6 and self.major < 3:
            s = f'oT{num}'
        elif rt in (11,12,13):
            s = f'c{num + 2048*(rt-10)}'
        else:
            s = f'{REG.get(rt, "?")}{num}'
        key = {2:'c',7:'i',14:'b',10:'s'}.get(rt)
        if key and (key, num) in self.names:
            s = f'{s}<{self.names[(key, num)]}>'
        if key == 'c' and num in self.defs:
            s = f'{s}{{{",".join("%g" % x for x in self.defs[num])}}}'
        if rel is not None:
            s = s + f'[{rel}]'
        return s

    def dst(self, t):
        m = (t >> 16) & 0xf
        mods = (t >> 20) & 0xf
        s = self.reg(t, False)
        if m != 0xf:
            s += '.' + ''.join('xyzw'[k] for k in range(4) if m & (1 << k))
        pre = ('_sat' if mods & 1 else '') + ('_pp' if mods & 2 else '') + ('_centroid' if mods & 4 else '')
        return s, pre

    def src(self, t, rel=None):
        sw = (t >> 16) & 0xff
        mod = (t >> 24) & 0xf
        s = self.reg(t, True, rel)
        comps = ''.join('xyzw'[(sw >> (2*k)) & 3] for k in range(4))
        if comps != 'xyzw':
            if len(set(comps)) == 1: comps = comps[0]
            s += '.' + comps
        return {0:'{}',1:'-{}',2:'{}_bias',3:'-{}_bias',4:'{}_bx2',5:'-{}_bx2',6:'1-{}',7:'{}_x2',8:'-{}_x2',
                9:'{}_dz',10:'{}_dw',11:'abs({})',12:'-abs({})',13:'!{}'}[mod].format(s)

    def disasm(self):
        out = [('ps' if self.ps else 'vs') + f'_{self.major}_{self.ver & 0xff}']
        # collect defs first so constants print inline
        for t, a in self.insts:
            if t & 0xffff == 81:
                self.defs[a[0] & 0x7ff] = struct.unpack('<4f', struct.pack('<4I', *a[1:5]))
        ind = 0
        for t, a in self.insts:
            op = t & 0xffff; ctl = (t >> 16) & 0xff
            name = OPS.get(op, f'op{op}')
            if op in (29, 39, 42, 43): ind -= 1
            pad = '  ' * max(ind, 0)
            if op == 31:
                d, pre = self.dst(a[1])
                if regtype(a[1]) == 10:
                    out.append(f'{pad}dcl_{TEXTYPE.get((a[0]>>27)&0xf,"?")} {d}')
                else:
                    u = USAGE.get(a[0] & 0x1f, '?'); ui = (a[0] >> 16) & 0xf
                    out.append(f'{pad}dcl_{u}{ui if ui else ""}{pre} {d}')
                continue
            if op == 81:
                continue
            if op in (47, 48):
                out.append(f'{pad}{name} {self.reg(a[0])}, {a[1:]}'); continue
            sfx = ''
            if op in (41, 45, 94): sfx = CMP.get(ctl, '')
            if op == 66 and ctl == 1: sfx = 'p'
            if op == 66 and ctl == 2: sfx = 'b'
            ops = []
            k = 0
            hasdst = op not in (25, 26, 27, 38, 40, 41, 45, 30, 65) and op not in NOOPERANDS
            if op == 65: hasdst = True
            pred = ''
            if t & (1 << 28):
                pass
            while k < len(a):
                tok = a[k]; k += 1
                rel = None
                if tok & (1 << 13) and self.major >= 3 or (tok & (1<<13) and regtype(tok)==2):
                    if k < len(a) and self.major >= 2:
                        rel = self.src(a[k]); k += 1
                if hasdst and not ops:
                    d, pre = self.dst(tok); sfx += pre; ops.append(d)
                else:
                    ops.append(self.src(tok, rel))
            if t & (1 << 28) and len(ops) >= 2:
                pred = f'({ops[-1]}) '; ops = ops[:-1]
            out.append(f'{pad}{pred}{name}{sfx} ' + ', '.join(ops))
            if op in (27, 38, 40, 41, 42): ind += 1
        return '\n'.join(out)
