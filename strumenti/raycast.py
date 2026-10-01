import bpy, sys, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
objpath = argv[0]; ex, ey, ez, tx, ty, tz, lens, W, H = [float(v) for v in argv[1].split(',')]
pix = [tuple(map(float, p.split(','))) for p in argv[2:]]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=objpath)
def B(x, y, z): return Vector((x, -z, y))
sc = bpy.context.scene
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = lens; cam.location = B(ex, ey, ez)
d = B(tx, ty, tz) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x = int(W); sc.render.resolution_y = int(H)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
M = cam.matrix_world
f = lens / 36.0 * W      # sensor fit auto: larghezza
for (px, py) in pix:
    for dy in range(-4, 5):
        x = (px - W / 2) / f; y = -((py + dy) - H / 2) / f
        dirc = (M.to_3x3() @ Vector((x, y, -1))).normalized()
        hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, cam.location, dirc)
        if hit:
            print(px, py + dy, ob.name, 'obj=(%.2f, %.2f, %.2f)' % (loc.x, loc.z, -loc.y), 'n=(%.2f,%.2f,%.2f)' % (nrm.x, nrm.z, -nrm.y), idx)
        else:
            print(px, py + dy, 'NIENTE (cielo)')
