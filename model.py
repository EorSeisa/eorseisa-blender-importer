import bpy

import numpy as np

from .utils import read_struct, open_hash, to_temp
from .material import read_kf_material


def read_kf_model(hash_, zf, parent):
    name, of = open_hash(hash_, zf)
    root = bpy.data.objects.find(name)
    if root > 0:
        m = bpy.data.objects[root].copy()
        parent.objects.link(m)
        return m

    f = to_temp(of)
    magic = f.read(4)

    vertex_count, index_count, material_count, using_mask = read_struct(f, "IIHH")

    materials = []
    for _ in range(material_count):
        m_hash, = read_struct(f, "Q")
        materials.append(read_kf_material(m_hash, zf))

    indices = np.fromfile(f, np.dtype('u2'), index_count)

    positions = np.fromfile(f, np.dtype('f4,f4,f4'), vertex_count)

    if using_mask & 0x02:
        blend_weights = np.fromfile(f, np.dtype('f4,f4,f4,f4'), vertex_count)
        print(f"WARNING: We don't support blend weights yet, and {name} uses them")
    else:
        blend_weights = None

    material_indices = np.array(np.fromfile(f, np.dtype('u4'), vertex_count)[indices][::3])

    if using_mask & 0x08:
        normals = np.fromfile(f, np.dtype('f4,f4,f4'), vertex_count)
    else:
        normals = None

    if using_mask & 0x10:
        uvs = np.fromfile(f, np.dtype('f4'), vertex_count * 2)
        uvs = np.reshape(uvs, (-1, 2))
        uvs = uvs[indices]
        uvs = uvs.flatten()
    else:
        uvs = None

    if using_mask & 0x80:
        colors = np.fromfile(f, np.dtype('f4'), vertex_count * 4)
        colors = np.reshape(colors, (-1, 4))
        colors = colors[indices]
        colors = colors.flatten()
    else:
        colors = np.repeat(1.0, index_count * 4)

    indices = np.reshape(indices, (-1, 3))

    mesh = bpy.data.meshes.new(f"{name}.mesh")

    for mat in materials:
        mesh.materials.append(mat)

    mesh.from_pydata(positions, [], indices)
    mesh.update()

    mesh.polygons.foreach_set("material_index", material_indices)
    if uvs is not None:
        layer = mesh.uv_layers.new()
        layer.data.foreach_set("uv", uvs)
    if normals is not None:
        mesh.create_normals_split()
        mesh.normals_split_custom_set_from_vertices(normals)
        mesh.use_auto_smooth = True
    if colors is not None:
        mesh.vertex_colors.new(name="KF_COLOR")
        mesh.vertex_colors["KF_COLOR"].data.foreach_set("color", colors)

    f.close()

    root = bpy.data.objects.new(name, mesh)
    parent.objects.link(root)

    return root
