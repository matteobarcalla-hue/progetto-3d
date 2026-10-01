import sys, numpy as np, math
sys.path.insert(0, 'tools')
import animali_gen as G
specs = [('cow', dict(col_corpo='fur_white')), ('cow', dict(col_corpo='fur_brown')), ('horse', dict(col_corpo='fur_brown', col_zampe='fur_black')),
         ('donkey', dict(col_corpo='fur_grey')), ('sheep', dict(col_corpo='wool_white', col_zampe='fur_black')), ('goat', dict(col_corpo='fur_white', col_zampe='fur_grey')),
         ('pig', dict(col_corpo='wall_plaster_rose')), ('deer', dict(col_corpo='fur_tan')), ('dog', dict(col_corpo='fur_brown', col_zampe='fur_black')),
         ('chicken', dict(col='feather_white')), ('chicken', dict(col='fur_brown')), ('duck', dict(col='fur_brown')), ('swan', dict(col='feather_white')),
         ('seagull', dict(vola=False)), ('seagull', dict(vola=True)),
         ('persona', dict(veste='flag_red', brache='fur_brown', pelle='wall_plaster_rose', capelli='fur_black')),
         ('persona', dict(veste='banner_blue', brache='fur_grey', pelle='wall_plaster_rose', capelli='fur_tan', gonna=True)),
         ('persona', dict(veste='flag_red', brache='fur_grey', pelle='wall_plaster_rose', capelli='fur_black', guardia=True)),
         ('persona', dict(veste='crop_green', brache='fur_brown', pelle='wall_plaster_rose', capelli='fur_black', cappello='hay'))]
Vs = []; Fs = []; Ms = []; x = 0.0
tot = {}
for tipo, kw in specs:
    parts = G.model(tipo, **kw)
    V, F, M = G.assemble(parts)
    tot[tipo] = len(F)
    # Blender (bx,by,bz) -> OBJ (x=bx, y=bz, z=-by); animale rivolto verso +Z OBJ (verso la camera)
    P = np.stack([V[:, 0] + x, V[:, 2], V[:, 1]], 1)
    b = len(Vs); Vs += P.tolist(); Fs += [[b + i for i in f] for f in F]; Ms += M
    x += 2.6 if tipo in ('cow', 'horse', 'donkey', 'deer') else 1.6
print(tot)
with open('test_animali.obj', 'w') as f:
    f.write('mtllib castello_mappa_estesa.mtl\no Test\n')
    for v in Vs: f.write('v %.4f %.4f %.4f\n' % tuple(v))
    cur = None
    for fc, m in zip(Fs, Ms):
        if m != cur: f.write('usemtl %s\n' % m); cur = m
        f.write('f ' + ' '.join(str(i + 1) for i in fc) + '\n')
    # suolo
    n = len(Vs)
    f.write('v -2 0 -3\nv 40 0 -3\nv 40 0 3\nv -2 0 3\nusemtl terrain_grass\nf %d %d %d %d\n' % (n + 1, n + 4, n + 3, n + 2))
print('x fine', x)
