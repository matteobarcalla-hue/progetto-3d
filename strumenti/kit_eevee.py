import bpy, sys, time, traceback
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
obj, kit, out, nebbia, ombre = argv[0], argv[1], argv[2], argv[3] == '1', argv[4] == '1'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj)
src = open(kit).read().replace('NEBBIA = True', 'NEBBIA = %s' % nebbia).replace('OMBRE_ALTA_QUALITA = True', 'OMBRE_ALTA_QUALITA = %s' % ombre)
src = src.replace('LUCE_CIELO = 1.0', 'LUCE_CIELO = 0.6').replace('ld.energy = 3.5', 'ld.energy = 4.0')
src = src.replace('ABITANTI = True', 'ABITANTI = False').replace('ANIMALI = True', 'ANIMALI = False')
exec(compile(src, kit, 'exec'), {'__name__': '__main__'})
sc = bpy.context.scene
sc.frame_set(700)
sc.view_settings.exposure = float(argv[5]) if len(argv) > 5 else 0.0
for lk in ((argv[6],) if len(argv) > 6 else ('AgX - Medium High Contrast',)):
    try:
        sc.view_settings.look = lk; print('look', lk); break
    except Exception as e: print('look no', lk, e)
print('camera', sc.camera.name, tuple(round(v, 1) for v in sc.camera.matrix_world.translation))
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = 640; sc.render.resolution_y = 360
try: sc.eevee.taa_render_samples = 8
except Exception: pass
sc.render.filepath = out; t = time.time(); bpy.ops.render.render(write_still=True); print('eevee %.1f s' % (time.time() - t))
import numpy as np
img = bpy.data.images.load(out); px = np.array(img.pixels[:]).reshape(-1, 4); print('media pixel', px[:, :3].mean(0))
