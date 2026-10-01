"""Prova del kit in Blender (bpy): python kit_test.py modello.obj kit.py [salva.blend]"""
import bpy, sys, time, traceback
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
obj, kit = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
t = time.time(); bpy.ops.wm.obj_import(filepath=obj); print('import %.1f s' % (time.time() - t))
src = open(kit).read()
t = time.time(); ok = True
try:
    exec(compile(src, kit, 'exec'), {'__name__': '__main__'})
except Exception:
    ok = False; traceback.print_exc()
print('kit %.1f s' % (time.time() - t), 'OK' if ok else 'ERRORE')
sc = bpy.context.scene
print('oggetti', len(bpy.data.objects), 'frame', sc.frame_start, sc.frame_end)
ts = []
for f in list(range(1, 11)) + [500, 501, 502, 1500, 1501]:
    t = time.time(); sc.frame_set(f); ts.append(time.time() - t)
print('tempo per fotogramma (valutazione scena, senza disegno): media %.3f s, max %.3f s' % (sum(ts[1:]) / (len(ts) - 1), max(ts[1:])))
if 'Kit_Log' in bpy.data.texts: print(bpy.data.texts['Kit_Log'].as_string())
if len(argv) > 2: bpy.ops.wm.save_as_mainfile(filepath=argv[2])
