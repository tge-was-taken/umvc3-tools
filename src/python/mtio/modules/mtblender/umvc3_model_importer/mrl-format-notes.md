# MRL format notes

## Header

| field | values seen | meaning |
|---|---|---|
| `type` | `nDraw::MaterialChar` (85), `nDraw::MaterialCharAlpha` (5) | Shader technique. Picks which `T*` entry in `UserShaderPackage.mfx` runs. |
| `blendState` | `BSSolid` (85), `BSBlendAlpha` (5) | `BSSolid` writes opaque, `BSBlendAlpha` composites, etc. |
| `rasterizerState` | `RSMesh` (85), `RSMeshCN` (5) | `RSMesh` culls backfaces. `RSMeshCN` is cull-none, used on two-sided pieces like Dante's coat tails. |
| `depthStencilState` | `DSZTestWriteStencilWrite` (90) | Depth test + write, stencil write. The stencil is what the outline detector reads later. **likely** |
| `cmdListFlags` | `0x0` (90) | **unknown** |
| `matFlags` | `0x8c800003` on characters | Bitfield. **unknown** |

`blendState` and `type` are alwats similiar. The five `BSBlendAlpha` materials are exactly the
five `MaterialCharAlpha` ones, so either can be used to detect transparency.

---

## Texture slots

| slot | count | feeds |
|---|---|---|
| `tAlbedoMap` | 87 | base colour, alpha channel used when blending |
| `tNormalMap` | 77 | tangent-space normal, alpha and green inverted |
| `tSpecularMap` | 70 | specular mask |
| `tToonMap` | 82 | 512×1 lighting ramp |
| `tToonRevMap` | 81 | 512×1 reverse ramp, for the unlit side |
| `tSphereMap` | 11 | matcap-style reflection, sampled by view normal so it has no UV channel |
| `tAlbedoBlendMap` | 5 | second albedo layered over the first, on its own UV channel |
| `tOcclusionMap` | — | baked lightmap, stage models |


Each `texture` command is usually followed by a `samplerstate` (filtering and wrap) and
a `FUV<slot>` flag naming its UV channel.

---

## Flags

### Which UV channel feeds a texture

| flag | values |
|---|---|
| `FUVAlbedoMap` | `FUVPrimary` (87) |
| `FUVNormalMap` | `FUVPrimary` (77) |
| `FUVSpecularMap` | `FUVPrimary` (69), `FUVViewNormal` (1) |
| `FUVAlbedoBlendMap` | `FUVSecondary` (5) |

`FUVViewNormal` is worth noting as it is one material that samples its specular map by view normal rather than a UV set, i.e. as a matcap.

### Which UV channels get an animated offset

| flag | values |
|---|---|
| `FUVTransformPrimary` | `FUVTransformPrimary` (63), `FUVTransformOffset` (27) |
| `FUVTransformSecondary` | `FUVTransformSecondary` (64), `FUVTransformOffset` (5), `FUVTransformOffset2` (21) |
| `FUVTransformUnique` | `FUVTransformUnique` (90) |
| `FUVTransformExtend` | `FUVTransformExtend` (90) |

`FUVTransformOffset` marks a channel as offsettable. It is **not** sufficient to detect
animation. The presence of `animData` is the actual marker. This is probably what's used for eye movement in character's like Zero

### Lighting model

| flag | values | meaning |
|---|---|---|
| `FBRDF` | `FToonShader` (82), `FBRDF` (7), `FToonShaderHigh` (1) | Which lighting model. Most characters are cel-shaded; `FBRDF` is the plain lit path. |
| `FToonLightCalc` | `FToonLightCalc` (48), `FToonLightCalcHalf` (34), `FToonLightCalcNone` (1) | How the ramp is sampled. The `Half` variant uses half-lambert, which is what `CBHalfLambert` parameterises. |
| `FToonLightRevCalc` | `FToonLightRevCalc` (46), `FToonLightRevCalcHalf` (35) | Same, for the reverse ramp |
| `FLighting` | `FLighting` (90) | Always on |
| `FAmbient` | `FAmbient` (4), `FAmbientSH` (1) | Spherical harmonics ambient on one material |

### Surface response

| flag | values | meaning |
|---|---|---|
| `FSpecular` | `FSpecularMaskToon` (69), `FSpecularDisable` (14), `FSpecular` (6), `FSpecularMap` (1) | **`FSpecularDisable` means no specular at all** |
| `FFresnel` | `FFresnel` (65), `FFresnelLegacy` (11) | Two implementations. A fresnel is a technique used in shaders to change a material's look based on the angle at which you look at it. |
| `FReflect` | `FReflect` (54), `FReflectSphereMap` (11), `FReflectGlobalCubeMap` (11) | Reflection source. |
| `FCalcRimLight` | `FCalcRimLight` (60), `FCalcRimLightDefault` (21), `FCalcRimLightNone` (2) | `None` means no rim light |
| `FBump` | `FBumpNormalMap` (77), `FBump` (13) | The 13 plain `FBump` materials have no normal map |
| `FAlbedo` | `FAlbedoMap` (82), `FAlbedoMapModulate` (5), `FAlbedo` (3) | `Modulate` is the blend-map path, matching the 5 `tAlbedoBlendMap` slots |
| `FDiffuse` | `FDiffuseColorCorectSimple` (59), `FDiffuseColorCorect` (24), `FDiffuse` (5), `FDiffuseConstant` (2) | The 24 `FDiffuseColorCorect` materials are exactly the 24 with a `CBDiffuseColorCorect` buffer |
| `FTransparency` | `FTransparency` (82), `FTransparencyAlpha` (8) |
| `FDistortion`, `FShininess`, `FVertexDisplacement` |

---

## Constant buffers

### `CBMaterial`

Only seven components ever differ across four characters:

| index | meaning |
|---|---|
| 0–2 | diffuse RGB multiplier |
| 4–6 | specular RGB tint |
| 7 | specular exponent |
| 15 | ties to UV animation |

### `CBHalfLambert`

`(bias, scale, 0, 0)`. The ramp is sampled at `N·L * scale + bias`. Per material art direction.

### `CBDiffuseColorCorect`

Flat albedo multiplier.

### `CBToon2`

Could control alternative toon shaders.

### `$Globals`

Catch-all material values.

---

## animData

A base64 string that diffs at 384 bytes or 304 bytes. Structure is a `0x40` header then N blocks of 80,
so `N = (len - 0x40) / 80`.

Often used for UV animation in material. (Beowulf, Ammy)


| offset | meaning |
|---|---|
| `0x94`, `0x98` | scroll vector as `(u, v)` |
| `0x10` | rate or period of change|
| `0x40`, `0x76`, `0x91` | block tags, vary but not decoded |
