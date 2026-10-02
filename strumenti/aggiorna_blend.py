"""Aggiorna il .blend dell'utente con il modello della fase 3, senza toccare il resto della scena.
- Ogni oggetto della mappa riceve la mesh nuova (stesso nome, stessa collezione, stessi materiali per nome).
- Oggetti nuovi (Borgo_Altopiano, Borgo_Porto, Pale_Dolomitiche) nella collezione della mappa.
- Oggetti rimasti vuoti (case sparse della fase 2) tolti.
- Materiali nuovi creati come gli altri (Principled, colore della vista Solida uguale).
- Cubo, luci, camera dell'utente, impostazioni della scena: invariati.
- Il kit v6 viene caricato come testo ed eseguito: rifà camere, persone, animali, luci con le impostazioni dell'utente.
Uso: venv/bin/python aggiorna_blend.py ingresso.blend stato.pkl kit_v6.py uscita.blend"""
import sys, pickle, time
import numpy as np
import bpy

ing, stato, kit, usc = sys.argv[1:5]
t0 = time.time()
bpy.ops.wm.open_mainfile(filepath=ing)
S = pickle.load(open(stato, 'rb'))
V = S['V']; objs = S['objs']
# il terreno nello stato è la griglia delle quote: la mesh si rigenera come nel salvataggio dell'OBJ
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import terrain
V, tobj = terrain.to_object(S['H'], S['M'], S['mats'], S['I0'], S['J0'], V)
for o in objs:
    if o['name'] == 'Terreno': o['faces'], o['mats'], o['smooth'] = tobj['faces'], tobj['mats'], tobj['smooth']
KIT = {'Kit_Camere', 'Kit_Abitanti', 'Kit_Animali', 'Kit_Percorsi', 'Kit_Luci', 'Kit_Riquadri'}
NUOVI_MAT = {'terrain_meadow_alpine': (0.70, 0.65, 0.33), 'terrain_bosco': (0.15, 0.27, 0.11), 'tree_bosco': (0.10, 0.23, 0.09)}

# materiali
def materiale(nome):
    m = bpy.data.materials.get(nome)
    if m: return m
    base = bpy.data.materials.get('terrain_meadow') if nome.startswith('terrain') else bpy.data.materials.get('tree_dark')
    m = base.copy(); m.name = nome
    col = NUOVI_MAT[nome]
    b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if b is not None:
        if b.inputs['Base Color'].is_linked:                    # texture del kit eventualmente rimaste: colore pieno
            for l in list(b.inputs['Base Color'].links): m.node_tree.links.remove(l)
        b.inputs['Base Color'].default_value = (col[0], col[1], col[2], 1.0)
    m.diffuse_color = (col[0], col[1], col[2], 1.0)
    for k in list(m.keys()):
        if k.startswith('kit'): del m[k]
    print('materiale nuovo', nome)
    return m

coll_mappa = None
for o in bpy.data.objects:
    if o.name == 'Terreno':
        coll_mappa = o.users_collection[0]; mw_mappa = o.matrix_world.copy(); break

n_agg = 0; n_new = 0; n_slot = 0
nomi_stato = set()
for o in objs:
    nm = o['name']
    if not o['faces']: continue
    nomi_stato.add(nm)
    F = o['faces']
    used = np.unique(np.concatenate([np.asarray(f) for f in F])) - 1
    rm = np.full(used.max() + 1, -1, np.int64); rm[used] = np.arange(len(used))
    P = V[used]
    Pb = np.stack([P[:, 0], -P[:, 2], P[:, 1]], 1)            # OBJ (y in alto) -> Blender (z in alto), coordinate del mondo
    ob = bpy.data.objects.get(nm)
    esiste = ob is not None and ob.type == 'MESH' and not any(c.name in KIT for c in ob.users_collection)
    # nel .blend gli oggetti della mappa hanno una rotazione propria (90 gradi su X dall'importazione OBJ):
    # la mesh va scritta nelle coordinate locali dell'oggetto, così la trasformazione dell'utente resta com'è
    Mw = np.array(ob.matrix_world) if esiste else np.array(mw_mappa)
    Mi = np.linalg.inv(Mw)
    Pb = Pb @ Mi[:3, :3].T + Mi[:3, 3]
    me = bpy.data.meshes.new(nm)
    loops = np.concatenate([rm[np.asarray(f) - 1] for f in F]).astype(np.int32)
    lt = np.array([len(f) for f in F], np.int32); ls = np.r_[0, np.cumsum(lt)[:-1]].astype(np.int32)
    me.vertices.add(len(Pb)); me.vertices.foreach_set('co', Pb.astype(np.float32).ravel())
    me.loops.add(len(loops)); me.loops.foreach_set('vertex_index', loops)
    me.polygons.add(len(F)); me.polygons.foreach_set('loop_start', ls); me.polygons.foreach_set('loop_total', lt)
    nomi_m = list(dict.fromkeys(o['mats']))
    for mn in nomi_m: me.materials.append(materiale(mn))
    idx = {mn: i for i, mn in enumerate(nomi_m)}
    me.polygons.foreach_set('material_index', np.array([idx[x] for x in o['mats']], np.int32))
    me.polygons.foreach_set('use_smooth', np.array(o['smooth'], bool))
    me.update(calc_edges=True); me.validate(verbose=False)
    if esiste:
        old = ob.data; ob.data = me
        if old.users == 0: bpy.data.meshes.remove(old)
        for sl in ob.material_slots:                          # materiali presi dalla mesh, nell'ordine nuovo
            if sl.link == 'OBJECT': sl.link = 'DATA'; n_slot += 1
        n_agg += 1
    else:
        ob = bpy.data.objects.new(nm, me); coll_mappa.objects.link(ob); n_new += 1
        ob.matrix_world = mw_mappa
        print('oggetto nuovo', nm)
# oggetti della mappa che non esistono più (rimasti vuoti)
tolti = []
for ob in list(bpy.data.objects):
    if ob.type != 'MESH' or any(c.name in KIT for c in ob.users_collection): continue
    if coll_mappa not in ob.users_collection: continue
    if ob.name in ('Cube',): continue
    if ob.name not in nomi_stato:
        tolti.append(ob.name); bpy.data.objects.remove(ob, do_unlink=True)
print('oggetti aggiornati %d, nuovi %d, tolti %s, slot materiale riportati alla mesh %d (%.0f s)' % (n_agg, n_new, tolti, n_slot, time.time() - t0))
# kit v6
testo = open(kit).read()
t = bpy.data.texts.get('kit_ripresa_mappa_v6.py') or bpy.data.texts.new('kit_ripresa_mappa_v6.py')
t.clear(); t.write(testo)
g = {'__name__': '__main__'}
exec(compile(testo, 'kit_ripresa_mappa_v6.py', 'exec'), g)
print('kit eseguito (%.0f s)' % (time.time() - t0))
bpy.ops.wm.save_as_mainfile(filepath=usc, compress=True)
print('salvato', usc, '(%.0f s)' % (time.time() - t0))
