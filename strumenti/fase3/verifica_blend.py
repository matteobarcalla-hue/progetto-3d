import bpy, sys, pickle, numpy as np, collections
sys.path.insert(0, 'tools')
bpy.ops.wm.open_mainfile(filepath='fase3/castello sul mare - fase 3.blend')
from stato import carica
import terrain
S = pickle.load(open('fase3/finale.obj.state.pkl', 'rb'))
V, tobj = terrain.to_object(S['H'], S['M'], S['mats'], S['I0'], S['J0'], S['V'])
objs = {o['name']: o for o in S['objs']}; objs['Terreno'] = dict(objs['Terreno'], faces=tobj['faces'], mats=tobj['mats'])
KIT = {'Kit_Camere', 'Kit_Abitanti', 'Kit_Animali', 'Kit_Percorsi', 'Kit_Luci', 'Kit_Riquadri'}
err = 0; n = 0; maxd = 0
for ob in bpy.data.objects:
    if ob.type != 'MESH' or any(c.name in KIT for c in ob.users_collection) or ob.name == 'Cube': continue
    o = objs.get(ob.name)
    if o is None or not o['faces']:
        print('nel blend ma non nello stato:', ob.name); err += 1; continue
    me = ob.data; n += 1
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    mw = np.array(ob.matrix_world); W = co @ mw[:3, :3].T + mw[:3, 3]
    used = np.unique(np.concatenate([np.asarray(f) for f in o['faces']])) - 1; P = V[used]
    Pb = np.stack([P[:, 0], -P[:, 2], P[:, 1]], 1)
    d = max(np.abs(W.min(0) - Pb.min(0)).max(), np.abs(W.max(0) - Pb.max(0)).max()); maxd = max(maxd, d)
    if len(me.polygons) != len(o['faces']) or d > 0.01:
        print('DIVERSO', ob.name, len(me.polygons), len(o['faces']), d); err += 1
    # materiali: conteggio facce per nome
    mi = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi)
    nomi = [ob.material_slots[i].material.name if ob.material_slots[i].material else None for i in range(len(ob.material_slots))]
    cb = collections.Counter(nomi[i] for i in mi); cs = collections.Counter(o['mats'])
    if cb != cs: print('MATERIALI DIVERSI', ob.name, (cb - cs).most_common(3), (cs - cb).most_common(3)); err += 1
nomi_stato = {k for k, o in objs.items() if o['faces']}
mancano = [k for k in nomi_stato if bpy.data.objects.get(k) is None]
print('oggetti mappa controllati', n, 'errori', err, 'mancanti', mancano, 'scarto massimo riquadri %.4f m' % maxd)
print('altri oggetti:', sorted(o.name for o in bpy.data.objects if o.type != 'MESH' and not any(c.name in KIT for c in o.users_collection)))
print('collezioni kit:', {c.name: len(c.objects) for c in bpy.data.collections if c.name in KIT})
print('testi:', [t.name for t in bpy.data.texts])
sc = bpy.context.scene; print('scena', sc.name, 'fps', sc.render.fps, 'frame', sc.frame_start, sc.frame_end, 'camera', sc.camera.name if sc.camera else None)
