import bpy, time, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
bpy.ops.mesh.primitive_cube_add()
cam=bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); cam.location=(5,-5,5); cam.rotation_euler=(1.0,0,0.78); sc.camera=cam
l=bpy.data.objects.new('sun', bpy.data.lights.new('sun','SUN')); sc.collection.objects.link(l)
sc.render.resolution_x=320; sc.render.resolution_y=240
for eng in ('BLENDER_WORKBENCH','BLENDER_EEVEE','CYCLES'):
    try:
        sc.render.engine=eng; sc.render.filepath=f'/tmp/claude-0/-home-user-progetto-3d/2486ec4e-e6b4-5772-9e93-a359f2842e62/scratchpad/t_{eng}.png'
        t=time.time(); bpy.ops.render.render(write_still=True); print(eng,'OK',time.time()-t)
    except Exception as e: print(eng,'FAIL',e)
