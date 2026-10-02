"""Uso: python render_views.py modello.obj prefisso [vista...]
Viste: nome=tipo:cx,cz,quota|dist... definite sotto."""
import bpy, sys, math, time
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
objpath, pref = argv[0], argv[1]
sel = argv[2:]
t=time.time()
pass
bpy.ops.wm.open_mainfile(filepath=objpath)
for ob in bpy.data.objects:
    if any(c.name.startswith('Kit_') for c in ob.users_collection) or ob.type in ('LIGHT',): ob.hide_render = True
for ob in list(bpy.data.objects):
    if ob.name in ('Cube',): ob.hide_render = True
print('import', time.time()-t)
sc = bpy.context.scene
def B(x, y, z): return Vector((x, -z, y))
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_shadows = True; sh.shadow_intensity = 0.45
sh.show_cavity = True; sh.cavity_type = 'WORLD'; sh.cavity_ridge_factor = 0.6; sh.cavity_valley_factor = 0.8
sh.show_specular_highlight = False
sc.display.light_direction = (0.45, -0.35, 0.85)
sc.display.shadow_focus = 0.2
sc.render.film_transparent = False
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.62, 0.75, 0.9)
try: sh.background_type = 'WORLD'
except Exception: pass
sc.display.render_aa = '5'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = 0.5; cam.data.clip_end = 6000
VIEWS = {
 # nome: (tipo, params)
 'top':      ('ortho', (-17, 23, 600, 1600, 1200)),
}
def add_view(spec):
    # spec forms: name=ortho:cx,cz,scale,w,h  |  name=persp:ex,ey,ez,tx,ty,tz,lens,w,h
    name, rest = spec.split('=', 1); kind, nums = rest.split(':'); n = [float(v) for v in nums.split(',')]
    return name, kind, n
for spec in sel:
    name, kind, n = add_view(spec)
    if kind == 'ortho':
        cx, cz, scale, W, H = n
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = scale
        cam.location = B(cx, 900, cz); cam.rotation_euler = (0, 0, 0)
        # alto immagine = +X (mare)  -> camera up = Blender +X
        cam.rotation_euler = (0, 0, -math.pi/2)
    else:
        ex, ey, ez, tx, ty, tz, lens, W, H = n
        cam.data.type = 'PERSP'; cam.data.lens = lens
        cam.location = B(ex, ey, ez)
        d = B(tx, ty, tz) - cam.location
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x = int(W); sc.render.resolution_y = int(H)
    sc.render.filepath = f'{pref}_{name}.png'
    t = time.time(); bpy.ops.render.render(write_still=True); print(name, 'render', round(time.time()-t, 1))
