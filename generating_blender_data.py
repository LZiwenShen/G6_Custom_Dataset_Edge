import bpy
import os
import math
from mathutils import Vector

output_root = "C:/Users/16693/OneDrive/Desktop/Blender"
num_views = 50
radius = 4.5
cam_height = 2.2
image_res = 512
target = Vector((0, 0, 0))
intrinsics = [512.0, 512.0, 256.0, 256.0]  # fx fy cx cy

def make_material_glass():
    mat = bpy.data.materials.new("Glass_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.5

    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (200, 0)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    return mat

def make_material_ceramic():
    mat = bpy.data.materials.new("Ceramic_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (0.72, 0.68, 0.6, 1)
    bsdf.inputs["Roughness"].default_value = 0.4

    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (200, 0)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    return mat

def make_material_metal():
    mat = bpy.data.materials.new("Metal_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.2
    bsdf.inputs["Transmission Weight"].default_value = 0.0
    bsdf.inputs["Base Color"].default_value = (0.3, 0.3, 0.3, 1)
    bsdf.inputs["Specular IOR Level"].default_value = 0.5

    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (200, 0)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    return mat

def write_intrinsics(scene_dir):
    with open(os.path.join(scene_dir, "intrinsic.txt"), 'w') as f:
        f.write("fx fy cx cy\n")
        f.write(" ".join([str(i) for i in intrinsics]))

def render_views(scene_dir, cam):
    R_path = os.path.join(scene_dir, "R_matrix.txt")
    T_path = os.path.join(scene_dir, "T_matrix.txt")
    R_file = open(R_path, 'w')
    T_file = open(T_path, 'w')

    for i in range(num_views):
        angle = i * 2 * math.pi / num_views
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        z = cam_height
        cam.location = (x, y, z)

        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

        R = cam.rotation_euler.to_matrix().transposed()
        T = cam.location

        for row in R:
            R_file.write(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f}\n")

        T_file.write(f"{T[0]:.6f} {T[1]:.6f} {T[2]:.6f}\n")

        bpy.context.scene.render.filepath = os.path.join(scene_dir, f"view_{i:03d}.png")
        bpy.ops.render.render(write_still=True)

    R_file.close()
    T_file.close()

materials = {
    "glass": make_material_glass(),
    "ceramic": make_material_ceramic(),
    "metal": make_material_metal(),
}

for name, mat in materials.items():
    scene_dir = os.path.join(output_root, name)
    os.makedirs(scene_dir, exist_ok=True)

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.6, depth=1.2, location=(0, 0, 0.6))
    cup = bpy.context.active_object
    cup.data.materials.append(mat)

    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -0.01))
    ground = bpy.context.active_object
    ground_mat = bpy.data.materials.new(name="WhiteGround")
    ground_mat.use_nodes = True
    nodes = ground_mat.node_tree.nodes
    links = ground_mat.node_tree.links
    nodes.clear()
    diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
    diffuse.inputs['Color'].default_value = (1, 1, 1, 1)
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])
    ground.data.materials.append(ground_mat)

    bpy.context.view_layer.objects.active = ground
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam
    cam.rotation_euler.x += 0.3

    bpy.ops.object.light_add(type='AREA', location=(5, -5, 5))
    light = bpy.context.active_object
    light.data.shape = 'RECTANGLE'
    light.data.size = 2.0
    light.data.size_y = 0.3
    light.data.energy = 1500

    direction = target - light.location
    light.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (1, 1, 1, 1)
    bg.inputs['Strength'].default_value = 2.0

    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    scene.cycles.use_soft_shadows = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.resolution_x = image_res
    scene.render.resolution_y = image_res
    scene.render.film_transparent = False

    write_intrinsics(scene_dir)
    render_views(scene_dir, cam)
