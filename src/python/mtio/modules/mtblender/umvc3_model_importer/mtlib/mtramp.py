import numpy as np

def _s(x, sw):
    """swizzle: x is (n,4), sw like 'yzxw'"""
    return x[:, ['xyzw'.index(c) for c in sw]]

def _w(dst, mask, val):
    for i, c in enumerate('xyzw'):
        if c in mask:
            dst[:, i] = val[:, i]

def _cmp(a, b, c):
    return np.where(a >= 0, b, c)

def toon_high(rgb, toon2):
    rgb = np.asarray(rgb, dtype=np.float64)
    n = rgb.shape[0]
    tx, ty, tz = float(toon2[0]), float(toon2[1]), float(toon2[2])
    one = lambda v: np.full((n, 4), float(v))
    c11 = np.tile([0.166667, 1.0, 0.0087265, 0.104718], (n, 1))
    c12 = np.tile([6.0, -5.0, 0.0, 0.0], (n, 1))
    c13 = np.tile([1.0, 0.0, 2.0, 4.0], (n, 1))
    c0 = np.tile([-1.0, -2.0, -3.0, -4.0], (n, 1))
    r0 = np.zeros((n, 4)); r1 = np.zeros((n, 4)); r2 = np.zeros((n, 4)); r3 = np.zeros((n, 4))
    r0[:, :3] = rgb
    # 177 mov_sat r0.xyz, r0.yzxw
    _w(r0, 'xyz', np.clip(_s(r0, 'yzxw'), 0, 1))
    # 178 add r1.xyz, -r0.yzxw, r0
    _w(r1, 'xyz', -_s(r0, 'yzxw') + r0)
    # 179 cmp r0.yw, r1.x, r0.xxzy, r0.xyzx
    _w(r0, 'yw', _cmp(_s(r1, 'xxxx'), _s(r0, 'xxzy'), _s(r0, 'xyzx')))
    # 180 min r1.w, r0.w, r0.z
    _w(r1, 'w', np.minimum(_s(r0, 'wwww'), _s(r0, 'zzzz')))
    # 181 max r2.x, r0.z, r0.y
    _w(r2, 'x', np.maximum(_s(r0, 'zzzz'), _s(r0, 'yyyy')))
    # 182 add r0.xy, r0.zxzw, -r2.x
    _w(r0, 'xy', _s(r0, 'zxzw') - _s(r2, 'xxxx'))
    # 183 add r0.z, -r1.w, r2.x
    _w(r0, 'z', -_s(r1, 'wwww') + _s(r2, 'xxxx'))
    # 184 rcp r0.w, r0.z
    z = _s(r0, 'zzzz')[:, :1]
    _w(r0, 'w', np.repeat(1.0 / np.where(z == 0, 1e-30, z), 4, 1))
    # 185 mad r1.yz, r1, r0.w, c13.xzww
    _w(r1, 'yz', r1 * _s(r0, 'wwww') + _s(c13, 'xzww'))
    # 186 mul r0.w, r0.w, r1.x
    _w(r0, 'w', _s(r0, 'wwww') * _s(r1, 'xxxx'))
    # 187 cmp r0.y, -abs(r0.y), r1.y, r1.z
    _w(r0, 'y', _cmp(-np.abs(_s(r0, 'yyyy')), _s(r1, 'yyyy'), _s(r1, 'zzzz')))
    # 188 cmp r0.x, -abs(r0.x), r0.w, r0.y
    _w(r0, 'x', _cmp(-np.abs(_s(r0, 'xxxx')), _s(r0, 'wwww'), _s(r0, 'yyyy')))
    # 189 mul r0.y, r0.x, c11.x
    _w(r0, 'y', _s(r0, 'xxxx') * _s(c11, 'xxxx'))
    # 190 mad r0.w, r0.x, c11.x, c11.y
    _w(r0, 'w', _s(r0, 'xxxx') * _s(c11, 'xxxx') + _s(c11, 'yyyy'))
    # 191 cmp_sat r0.x, r0.x, r0.y, r0.w
    _w(r0, 'x', np.clip(_cmp(_s(r0, 'xxxx'), _s(r0, 'yyyy'), _s(r0, 'wwww')), 0, 1))
    # 192 mov r1.zw, c11
    _w(r1, 'zw', c11)
    # 193 mad r0.x, CBToon2.x, r1.w, r0.x
    _w(r0, 'x', tx * _s(r1, 'wwww') + _s(r0, 'xxxx'))
    # 194 mul r0.y, r0.x, c11.x
    _w(r0, 'y', _s(r0, 'xxxx') * _s(c11, 'xxxx'))
    # 195 mad r0.w, r0.x, c11.x, c11.y
    _w(r0, 'w', _s(r0, 'xxxx') * _s(c11, 'xxxx') + _s(c11, 'yyyy'))
    # 196 cmp r0.x, r0.x, r0.y, r0.w
    _w(r0, 'x', _cmp(_s(r0, 'xxxx'), _s(r0, 'yyyy'), _s(r0, 'wwww')))
    # 197 add r0.y, r0.x, -c13.x
    _w(r0, 'y', _s(r0, 'xxxx') - _s(c13, 'xxxx'))
    # 198 cmp r0.x, r0.y, r0.y, r0.x
    _w(r0, 'x', _cmp(_s(r0, 'yyyy'), _s(r0, 'yyyy'), _s(r0, 'xxxx')))
    # 199 mul r0.y, r0.x, c12.x
    _w(r0, 'y', _s(r0, 'xxxx') * _s(c12, 'xxxx'))
    # 200 frc r0.w, r0.y
    y = _s(r0, 'yyyy'); _w(r0, 'w', y - np.floor(y))
    # 201 add r0.y, -r0.w, r0.y
    _w(r0, 'y', -_s(r0, 'wwww') + _s(r0, 'yyyy'))
    # 202 add r0.w, r0.y, c12.y
    _w(r0, 'w', _s(r0, 'yyyy') + _s(c12, 'yyyy'))
    # 203 mad r0.x, r0.x, c12.x, -r0.y
    _w(r0, 'x', _s(r0, 'xxxx') * _s(c12, 'xxxx') - _s(r0, 'yyyy'))
    # 204 add r3, r0.y, c0
    r3 = _s(r0, 'yyyy') + c0
    # 205 add r0.y, -r0.x, c13.x
    _w(r0, 'y', -_s(r0, 'xxxx') + _s(c13, 'xxxx'))
    # 206 rcp r1.x, r2.x
    x2 = _s(r2, 'xxxx')[:, :1]
    _w(r1, 'x', np.repeat(1.0 / np.where(x2 == 0, 1e-30, x2), 4, 1))
    # 207 mul r0.z, r0.z, r1.x
    _w(r0, 'z', _s(r0, 'zzzz') * _s(r1, 'xxxx'))
    # 208 cmp r0.z, -r2.x, c13.y, r0.z
    _w(r0, 'z', _cmp(-_s(r2, 'xxxx'), _s(c13, 'yyyy'), _s(r0, 'zzzz')))
    # 209 mad_sat r2.y, CBToon2.z, r1.z, r2.x
    _w(r2, 'y', np.clip(tz * _s(r1, 'zzzz') + _s(r2, 'xxxx'), 0, 1))
    # 210 mad_sat r0.z, CBToon2.y, r1.z, r0.z
    _w(r0, 'z', np.clip(ty * _s(r1, 'zzzz') + _s(r0, 'zzzz'), 0, 1))
    # 211 add r0.z, -r2.y, r0.z
    _w(r0, 'z', -_s(r2, 'yyyy') + _s(r0, 'zzzz'))
    # 212 max r1.x, r0.z, c13.y
    _w(r1, 'x', np.maximum(_s(r0, 'zzzz'), _s(c13, 'yyyy')))
    # 213 mad r0.y, r1.x, -r0.y, c13.x
    _w(r0, 'y', _s(r1, 'xxxx') * -_s(r0, 'yyyy') + _s(c13, 'xxxx'))
    # 214 mad r0.x, r1.x, -r0.x, c13.x
    _w(r0, 'x', _s(r1, 'xxxx') * -_s(r0, 'xxxx') + _s(c13, 'xxxx'))
    # 215 mul r2.xz, r0.yyxw, r2.y
    _w(r2, 'xz', _s(r0, 'yyxw') * _s(r2, 'yyyy'))
    # 216 cmp r0.xz, r0.w, r2.yyzw, r2.xyyw
    _w(r0, 'xz', _cmp(_s(r0, 'wwww'), _s(r2, 'yyzw'), _s(r2, 'xyyw')))
    # 217 add r0.w, -r1.x, c13.x
    _w(r0, 'w', -_s(r1, 'xxxx') + _s(c13, 'xxxx'))
    # 218 mul r0.y, r0.w, r2.y
    _w(r0, 'y', _s(r0, 'wwww') * _s(r2, 'yyyy'))
    # 219 mov r2.w, r0.y
    _w(r2, 'w', _s(r0, 'yyyy'))
    # 220-223 cmp chain
    _w(r0, 'xyz', _cmp(_s(r3, 'wwww'), r0, _s(r2, 'wzyw')))
    _w(r0, 'xyz', _cmp(_s(r3, 'zzzz'), r0, _s(r2, 'wyxw')))
    _w(r0, 'xyz', _cmp(_s(r3, 'yyyy'), r0, _s(r2, 'zyww')))
    _w(r0, 'xyz', _cmp(_s(r3, 'xxxx'), r0, _s(r2, 'yxww')))
    # 224 cmp_sat r0.xyz, -r1.x, r2.y, r0
    _w(r0, 'xyz', np.clip(_cmp(-_s(r1, 'xxxx'), _s(r2, 'yyyy'), r0), 0, 1))
    return r0[:, :3]
