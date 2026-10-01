"""Prova del kit v5 sul modello della fase 2: esecuzione completa, fotogrammi dalle camere nuove (Workbench) e uno Eevee."""
import bpy, sys, time
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
obj, kit, pref = argv[0], argv[1], argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj)
exec(compile(open(kit).read(), kit, 'exec'), {'__name__': '__main__'})
sc = bpy.context.scene
mk = {m.name: (m.frame, m.camera) for m in sc.timeline_markers}
print('marcatori', sorted((v[0], k) for k, v in mk.items()), 'fine', sc.frame_end)
def shot(cam, fr, name, eng='BLENDER_WORKBENCH', W=1000, H=562):
    sc.frame_set(fr); sc.camera = cam
    sc.render.engine = eng; sc.render.resolution_x = W; sc.render.resolution_y = H; sc.render.resolution_percentage = 100
    if eng == 'BLENDER_WORKBENCH':
        sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_shadows = True; sh.show_cavity = True
    sc.render.filepath = '%s_%s.png' % (pref, name); t = time.time(); bpy.ops.render.render(write_still=True); print(name, eng, 'render %.1f s' % (time.time() - t))
for nome, offs in (() if argv[-1] == 'eevee08' else (('08_Scala_del_mago', (60, 200, 300)),) if len(sys.argv) > 4 and argv[-1] == 'solo08' else (('08_Scala_del_mago', (10, 160, 315)), ('09_Terre_nuove', (10, 250, 490)))):
    f0, cam = mk[nome]
    for k, o in enumerate(offs): shot(cam, f0 + o, '%s_%d' % (nome[:2], k))
f0, cam = mk['08_Scala_del_mago']
if argv[-1] == 'solo08': sys.exit(0)
try: shot(cam, f0 + 240, '08_eevee', eng='BLENDER_EEVEE_NEXT', W=960, H=540)
except Exception:
    try: shot(cam, f0 + 240, '08_eevee', eng='BLENDER_EEVEE', W=960, H=540)
    except Exception as e: print('eevee non riuscito', e)
