import bpy

_OP = {
    'add': ('ADD', 2), 'mul': ('MULTIPLY', 2), 'max': ('MAXIMUM', 2), 'min': ('MINIMUM', 2),
    'frc': ('FRACT', 1), 'sqrt': ('SQRT', 1), 'abs': ('ABSOLUTE', 1),
}


class Emitter:
    def __init__(self, tree, b, bind, x0=-4000, y0=0):
        self.tree = tree
        self.nodes = tree.nodes
        self.links = tree.links
        self.b = b
        self.g = b.g
        self.bind = bind
        self.sock = {}          # ir node id -> socket or float
        self.depth = {}
        self.rows = {}
        self.x0, self.y0 = x0, y0
        self.tex = {}           # ir tex id -> (color, alpha, separate)
        self.created = 0
        self.external = set()

    def _place(self, node, depth):
        r = self.rows.get(depth, 0)
        self.rows[depth] = r + 1
        node.location = (self.x0 + depth * 170, self.y0 - r * 40)
        node.hide = True
        self.created += 1

    def _feed(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            self.links.new(v, sock)
        else:
            sock.default_value = float(v)

    def math(self, op, *args, depth=0):
        n = self.nodes.new('ShaderNodeMath')
        n.operation = op
        for i, a in enumerate(args):
            self._feed(n.inputs[i], a)
        self._place(n, depth)
        return n.outputs[0]

    def mixf(self, fac, a, b, depth=0):
        """fac 0 -> a, 1 -> b"""
        n = self.nodes.new('ShaderNodeMix')
        n.data_type = 'FLOAT'
        n.clamp_factor = True
        self._feed(n.inputs[0], fac)
        self._feed(n.inputs[2], a)
        self._feed(n.inputs[3], b)
        self._place(n, depth)
        return n.outputs[0]

    def needed(self, roots=None):
        want = set()
        if roots is None:
            roots = [x for v in self.b.outputs.values() for x in v]
            if self.b.kill is not None:
                roots.append(self.b.kill)
        stack = list(roots)
        while stack:
            i = stack.pop()
            if i in want:
                continue
            want.add(i)
            node = self.g.nodes[i]
            if node[0] == 'op':
                stack.extend(node[2:])
            elif node[0] == 'tex':
                if i not in self.external:
                    stack.extend(node[3])
            elif node[0] == 'texc':
                stack.append(node[1])
        return sorted(want)

    def d(self, *ids):
        return 1 + max([self.depth.get(i, 0) for i in ids] or [0])

    def emit_roots(self, roots):
        self._emit_ids(self.needed(roots))
        return [self.sock[r] for r in roots]

    def emit(self):
        self._emit_ids(self.needed())
        out = {k: [self.sock[x] for x in v] for k, v in self.b.outputs.items()}
        kill = self.sock[self.b.kill] if self.b.kill is not None else None
        return out, kill

    def _emit_ids(self, ids):
        for i in ids:
            if i in self.sock or i in self.tex:
                continue
            node = self.g.nodes[i]
            kind = node[0]
            if kind == 'k':
                self.sock[i] = node[1]; self.depth[i] = 0
            elif kind == 'c':
                self.sock[i] = self.bind.const(node[1], node[2]); self.depth[i] = 0
            elif kind == 'v':
                self.sock[i] = self.bind.input(node[1], node[2]); self.depth[i] = 0
            elif kind == 'vface':
                self.sock[i] = self.bind.vface(); self.depth[i] = 0
            elif kind == 'vpos':
                self.sock[i] = self.bind.vpos(node[1]); self.depth[i] = 0
            elif kind == 'tex' and i in self.external:
                color, alpha = self.bind.external_texture(i, node[1])
                sep = self.nodes.new('ShaderNodeSeparateColor')
                self.links.new(color, sep.inputs[0])
                self._place(sep, 1)
                self.tex[i] = (sep, alpha)
                self.depth[i] = 1
            elif kind == 'tex':
                coords = [self.sock[x] for x in node[3]]
                dep = self.d(*node[3])
                color, alpha = self.bind.texture(node[1], node[2], coords, (self.x0 + dep * 170, self.y0 + 400))
                sep = self.nodes.new('ShaderNodeSeparateColor')
                self.links.new(color, sep.inputs[0])
                self._place(sep, dep + 1)
                self.tex[i] = (sep, alpha)
                self.depth[i] = dep + 1
            elif kind == 'texc':
                sep, alpha = self.tex[node[1]]
                self.sock[i] = alpha if node[2] == 3 else sep.outputs[node[2]]
                self.depth[i] = self.depth[node[1]]
            elif kind == 'op':
                self.sock[i] = self.op(node[1], [self.sock[x] for x in node[2:]], self.d(*node[2:]))
                self.depth[i] = self.d(*node[2:]) + (1 if node[1] in ('rsq', 'log2', 'pow', 'sel', 'ge', 'le', 'ne') else 0)

    def op(self, name, a, dep):
        if name in _OP:
            op, n = _OP[name]
            return self.math(op, *a[:n], depth=dep)
        if name == 'neg':
            return self.math('MULTIPLY', a[0], -1.0, depth=dep)
        if name == 'rcp':
            return self.math('DIVIDE', 1.0, a[0], depth=dep)
        if name == 'rsq':
            return self.math('INVERSE_SQRT', self.math('ABSOLUTE', a[0], depth=dep), depth=dep + 1)
        if name == 'exp2':
            return self.math('POWER', 2.0, a[0], depth=dep)
        if name == 'log2':
            return self.math('LOGARITHM', self.math('ABSOLUTE', a[0], depth=dep), 2.0, depth=dep + 1)
        if name == 'pow':
            return self.math('POWER', self.math('ABSOLUTE', a[0], depth=dep), a[1], depth=dep + 1)
        if name == 'sel':        # a >= 0 ? b : c
            return self.mixf(self.math('LESS_THAN', a[0], 0.0, depth=dep), a[1], a[2], depth=dep + 1)
        if name == 'mix':        # t ? b : a
            return self.mixf(a[0], a[1], a[2], depth=dep)
        if name == 'lt':
            return self.math('LESS_THAN', a[0], a[1], depth=dep)
        if name == 'gt':
            return self.math('GREATER_THAN', a[0], a[1], depth=dep)
        if name == 'ge':
            return self.math('SUBTRACT', 1.0, self.math('LESS_THAN', a[0], a[1], depth=dep), depth=dep + 1)
        if name == 'le':
            return self.math('SUBTRACT', 1.0, self.math('GREATER_THAN', a[0], a[1], depth=dep), depth=dep + 1)
        if name == 'eq':
            return self.math('COMPARE', a[0], a[1], 0.0, depth=dep)
        if name == 'ne':
            return self.math('SUBTRACT', 1.0, self.math('COMPARE', a[0], a[1], 0.0, depth=dep), depth=dep + 1)
        raise NotImplementedError(name)


def independent_textures(b):
    g = b.g
    # ids are created children first, so one forward pass settles every node
    dep = [False] * len(g.nodes)
    for i, node in enumerate(g.nodes):
        if node[0] in ('tex', 'texc'):
            dep[i] = True
        elif node[0] == 'op':
            dep[i] = any(dep[x] for x in node[2:])
    out = {}
    for i, node in enumerate(g.nodes):
        if node[0] == 'tex' and not any(dep[x] for x in node[3]):
            out[i] = node[1]
    return out


def emit(tree, b, bind, x0=-4000, y0=0, external=None):
    e = Emitter(tree, b, bind, x0, y0)
    e.external = set(external or ())
    out, kill = e.emit()
    return out, kill, e
