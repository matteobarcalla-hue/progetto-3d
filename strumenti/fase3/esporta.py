import bpy, numpy as np, pickle
bpy.ops.wm.open_mainfile(filepath='fase3/castello sul mare.blend')
out = {}
kit = {'Kit_Camere', 'Kit_Abitanti', 'Kit_Animali', 'Kit_Percorsi', 'Kit_Luci', 'Kit_Riquadri'}
for ob in bpy.data.objects:
    if ob.type != 'MESH' or any(c.name in kit for c in ob.users_collection): continue
    me = ob.data; mw = np.array(ob.matrix_world)
    n = len(me.vertices); co = np.empty(n * 3, np.float64); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    co = co @ mw[:3, :3].T + mw[:3, 3]
    obj = np.stack([co[:, 0], co[:, 2], -co[:, 1]], 1)   # Blender -> OBJ (y in alto)
    np_ = len(me.polygons)
    ls = np.empty(np_, np.int32); lt = np.empty(np_, np.int32); me.polygons.foreach_get('loop_start', ls); me.polygons.foreach_get('loop_total', lt)
    lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
    mi = np.empty(np_, np.int32); me.polygons.foreach_get('material_index', mi)
    sm = np.empty(np_, bool); me.polygons.foreach_get('use_smooth', sm)
    mats = [m.name if m else None for m in me.materials]
    out[ob.name] = dict(V=obj, ls=ls, lt=lt, lv=lv, mi=mi, sm=sm, mats=mats, hide=ob.hide_viewport, mw=mw)
pickle.dump(out, open('fase3/blend_mesh.pkl', 'wb'))
print('oggetti', len(out))
# materiali: colori diffusi per confronto
col = {}
for m in bpy.data.materials:
    if m.node_tree:
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if b: col[m.name] = tuple(round(x, 3) for x in b.inputs['Base Color'].default_value)
pickle.dump(col, open('fase3/blend_mat.pkl', 'wb'))
for t in bpy.data.texts:
    if t.name == 'Text': print('TEXT>>', t.as_string()[:3000])
k = bpy.data.texts.get('kit_ripresa_mappa (3).py')
if k:
    s = k.as_string(); print('KIT HEAD>>'); print('\n'.join(s.splitlines()[:60]))
w = bpy.context.scene.world
print('WORLD nodes', [(n.name, n.type) for n in w.node_tree.nodes] if w and w.node_tree else None)
