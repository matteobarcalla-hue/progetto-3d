"""Primi piani di persone e animali del kit in movimento (Workbench) + un fotogramma Eevee per le texture."""
import bpy, sys, time, math, traceback
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
obj, kit, pref = argv[0], argv[1], argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj)
exec(compile(open(kit).read(), kit, 'exec'), {'__name__': '__main__'})
sc = bpy.context.scene
for mk in list(sc.timeline_markers): sc.timeline_markers.remove(mk)
cam = bpy.data.objects.new('camprova', bpy.data.cameras.new('camprova')); sc.collection.objects.link(cam)
cam.data.clip_start = 0.05; cam.data.clip_end = 3000
def shot(target, fr, dist, h, lens, name, eng='BLENDER_WORKBENCH', W=900, H=600, side=1.0):
    sc.frame_set(fr); sc.camera = cam
    ob = bpy.data.objects[target]; p = ob.matrix_world.translation.copy()
    fwd = ob.matrix_world.to_3x3() @ Vector((0, 1, 0)); fwd.z = 0; fwd.normalize()
    rgt = Vector((fwd.y, -fwd.x, 0))
    cam.location = p + rgt * dist * side + fwd * dist * 0.35 + Vector((0, 0, h))
    tgt = p + Vector((0, 0, h * 0.45))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
    sc.render.engine = eng; sc.render.resolution_x = W; sc.render.resolution_y = H
    if eng == 'BLENDER_WORKBENCH':
        sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_shadows = True; sh.show_cavity = True
    sc.render.filepath = '%s_%s.png' % (pref, name); t = time.time(); bpy.ops.render.render(write_still=True); print(name, eng, 'render %.1f s' % (time.time() - t))
for i, (t, fr, d, h) in enumerate([('Persona_05', 700, 3.2, 1.3), ('Persona_11', 1203, 3.2, 1.3), ('Guardia_0', 800, 3.5, 1.5), ('Animale_024_cow', 640, 4.5, 1.6),
                                   ('Animale_061_horse', 905, 5.0, 1.8), ('Animale_008_chicken', 330, 1.4, 0.6)]):
    if t in bpy.data.objects: shot(t, fr, d, h, 35, 'wb%d' % i)
    else: print('manca', t)
# un fotogramma Eevee dalla camera 02 per vedere luce e texture
try:
    sc.eevee.taa_render_samples = 16
except Exception: pass
c2 = bpy.data.objects.get('02_Giro_fortezza')
if c2:
    sc.camera = c2; sc.frame_set(700)
    sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = 1280; sc.render.resolution_y = 720
    sc.render.filepath = pref + '_eevee.png'; t = time.time()
    try:
        bpy.ops.render.render(write_still=True); print('eevee render %.1f s' % (time.time() - t))
    except Exception: traceback.print_exc()
