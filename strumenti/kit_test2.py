"""Prova del kit v4: errori, espressioni semplici, tempi per fotogramma, render di controllo in Workbench."""
import bpy, sys, time, traceback, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
obj, kit, pref = argv[0], argv[1], argv[2]
views = argv[3:]
bpy.ops.wm.read_factory_settings(use_empty=True)
t = time.time(); bpy.ops.wm.obj_import(filepath=obj); print('import %.1f s' % (time.time() - t))
t = time.time(); ok = True
try:
    exec(compile(open(kit).read(), kit, 'exec'), {'__name__': '__main__'})
except Exception:
    ok = False; traceback.print_exc()
print('kit %.1f s' % (time.time() - t), 'OK' if ok else 'ERRORE')
sc = bpy.context.scene
nd = ns = 0; nonsimple = set()
for ob in bpy.data.objects:
    ad = ob.animation_data
    if ad:
        for fc in ad.drivers:
            nd += 1
            if fc.driver.is_simple_expression: ns += 1
            else: nonsimple.add(fc.driver.expression[:60])
print('oggetti', len(bpy.data.objects), 'mesh', len(bpy.data.meshes), 'driver', nd, 'semplici', ns, 'esempi non semplici', list(nonsimple)[:3])
ts = []
for f in list(range(1, 11)) + [500, 501, 502, 1500, 1501, 3000, 3001]:
    t = time.time(); sc.frame_set(f); ts.append(time.time() - t)
print('tempo per fotogramma (valutazione, senza disegno): media %.3f s, max %.3f s' % (sum(ts[1:]) / (len(ts) - 1), max(ts[1:])))
if 'Kit_Log' in bpy.data.texts: print(bpy.data.texts['Kit_Log'].as_string())
# render di controllo
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_shadows = True; sh.show_cavity = True
sc.display.light_direction = (0.45, -0.35, 0.85)
cam = bpy.data.objects.new('camprova', bpy.data.cameras.new('camprova')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = 0.1; cam.data.clip_end = 3000
def B(x, y, z): return Vector((x, -z, y))
for mk in list(sc.timeline_markers): sc.timeline_markers.remove(mk)
for spec in views:
    name, rest = spec.split('=', 1); fr, nums = rest.split(':'); n = [float(v) for v in nums.split(',')]
    ex, ey, ez, tx, ty, tz, lens, W, H = n
    sc.frame_set(int(fr)); sc.camera = cam
    cam.data.lens = lens; cam.location = B(ex, ey, ez)
    cam.rotation_euler = (B(tx, ty, tz) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x = int(W); sc.render.resolution_y = int(H); sc.render.filepath = '%s_%s.png' % (pref, name)
    bpy.ops.render.render(write_still=True)
