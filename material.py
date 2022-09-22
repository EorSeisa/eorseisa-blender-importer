import bpy

from json import load

from .utils import read_struct, open_hash
from .texture import read_kf_texture


def create_shader_group(diffuse_id, specular_id, normal_id, name, has_transparency, zf):
    group = bpy.data.node_groups.new(name, "ShaderNodeTree")
    group_output = group.nodes.new("NodeGroupOutput")
    group_output.location = (1500 if has_transparency else 1200, 200)

    diffuse_t = group.nodes.new("ShaderNodeTexImage")
    diffuse_t.location = (0, 300)
    diffuse_t.image = read_kf_texture(diffuse_id, zf)
    diffuse_t.label = "DIFFUSE"

    vert_color = group.nodes.new("ShaderNodeVertexColor")
    vert_color.layer_name = "KF_COLOR"
    vert_color.location = (0, 600)

    if False:  # TODO: Figure out when we need this
        diffuse = group.nodes.new("ShaderNodeMixRGB")
        diffuse.blend_type = "MULTIPLY"
        group.links.new(diffuse.inputs[1], diffuse_t.outputs["Color"])
        group.links.new(diffuse.inputs[2], vert_color.outputs["Color"])
    else:
        diffuse = diffuse_t

    specular = None
    if specular_id is not None:
        specular = group.nodes.new("ShaderNodeTexImage")
        specular.location = (0, 0)
        specular.image = read_kf_texture(specular_id, zf)
        specular.image.colorspace_settings.name = "Non-Color"
        specular.label = "SPECULAR"
        specular_inv = group.nodes.new("ShaderNodeInvert")
        specular_inv.location = (300, 0)
        group.links.new(specular_inv.inputs["Color"], specular.outputs["Color"])
        specular = specular_inv

    normal = None
    if normal_id is not None:
        normal = group.nodes.new("ShaderNodeTexImage")
        normal.location = (0, -300)
        normal.image = read_kf_texture(normal_id, zf)
        normal.image.colorspace_settings.name = "Non-Color"
        normal.label = "NORMAL"
        normal_map = group.nodes.new("ShaderNodeNormalMap")
        normal_map.location = (300, -300)
        normal_map.inputs["Strength"].default_value = 0.4
        group.links.new(normal_map.inputs["Color"], normal.outputs["Color"])
        normal = normal_map

    glossy_s = group.nodes.new("ShaderNodeBsdfGlossy")
    glossy_s.location = (600, 300)
    diffuse_s = group.nodes.new("ShaderNodeBsdfDiffuse")
    diffuse_s.location = (600, 0)

    group.links.new(glossy_s.inputs["Color"], diffuse.outputs["Color"])
    group.links.new(diffuse_s.inputs["Color"], diffuse.outputs["Color"])

    if specular:
        group.links.new(glossy_s.inputs["Roughness"], specular.outputs["Color"])
        group.links.new(diffuse_s.inputs["Roughness"], specular.outputs["Color"])

    if normal:
        group.links.new(glossy_s.inputs["Normal"], normal.outputs["Normal"])
        group.links.new(diffuse_s.inputs["Normal"], normal.outputs["Normal"])

    add_s = group.nodes.new("ShaderNodeAddShader")
    add_s.location = (900, 0)
    group.links.new(add_s.inputs[0], glossy_s.outputs["BSDF"])
    group.links.new(add_s.inputs[1], diffuse_s.outputs["BSDF"])

    if has_transparency:
        transparent_s = group.nodes.new("ShaderNodeBsdfTransparent")
        transparent_s.location = (900, -300)
        mix_s = group.nodes.new("ShaderNodeMixShader")
        mix_s.location = (1200, 0)
        group.links.new(mix_s.inputs["Fac"], diffuse_t.outputs["Alpha"])
        group.links.new(mix_s.inputs[1], transparent_s.outputs["BSDF"])
        group.links.new(mix_s.inputs[2], add_s.outputs["Shader"])
        group.links.new(group_output.inputs[0], mix_s.outputs["Shader"])
    else:
        group.links.new(group_output.inputs[0], add_s.outputs["Shader"])

    return group


def read_kf_material(hash_, zf):
    name, f = open_hash(hash_, zf)

    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat

    json = load(f)
    f.close()

    has_transparency = json["props"]["transparencyEnabled"]

    sampler_0 = json["samplers"][0]

    mat = bpy.data.materials.new(name)
    mat.use_backface_culling = json["props"]["backfaceCulling"]
    mat.shadow_method = mat.blend_method = "CLIP" if has_transparency else "OPAQUE"

    mat.use_nodes = True
    mat.node_tree.nodes.clear()

    for k, v in json["props"].items():
        mat["KF_" + k] = v
    for k, v in json["constants"].items():
        mat["KF_C_" + k] = v

    if sampler_0["diffuse"] is None:
        return mat

    shader_primary_g = create_shader_group(sampler_0["diffuse"], sampler_0["specular"], sampler_0["normal"],
                                           f"KF_SHDR_{hash_:016X}_0",
                                           has_transparency, zf)
    shader_primary = mat.node_tree.nodes.new("ShaderNodeGroup")
    shader_primary.node_tree = shader_primary_g
    mix_output = shader_primary

    if json["props"]["multipleTextures"]:
        sampler_1 = json["samplers"][1]
        shader_secondary_g = create_shader_group(sampler_1["diffuse"], sampler_1["specular"], sampler_1["normal"],
                                                 f"KF_SHDR_{hash_:016X}_1",
                                                 has_transparency, zf)
        shader_secondary = mat.node_tree.nodes.new("ShaderNodeGroup")
        shader_secondary.node_tree = shader_secondary_g

        blend_attr = mat.node_tree.nodes.new("ShaderNodeVertexColor")
        blend_attr.layer_name = "KF_COLOR"

        mix_node = mat.node_tree.nodes.new("ShaderNodeMixShader")
        mat.node_tree.links.new(mix_node.inputs["Fac"], blend_attr.outputs["Alpha"])
        mat.node_tree.links.new(mix_node.inputs[1], shader_primary.outputs[0])
        mat.node_tree.links.new(mix_node.inputs[2], shader_secondary.outputs[0])
        mix_output = mix_node

    output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    output.is_active_output = True
    output.location = (300, 0)

    mat.node_tree.links.new(output.inputs["Surface"], mix_output.outputs[0])

    return mat
