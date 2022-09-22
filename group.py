import bpy

from json import load
from math import radians
from mathutils import Matrix

from .shared_group import read_kf_shgroup
from .utils import decompose_matrix, open_json
from .model import read_kf_model

_LIGHT_TYPE_MAP = {
    0x1: "AREA",
    0x2: "POINT",
    0x3: "SPOT"
}


def _read_group_bg(obj, zf, parent):
    if "asset" not in obj["data"]:
        return
    mdl = read_kf_model(obj["data"]["asset"], zf, parent)
    mdl.location, mdl.rotation_euler, mdl.scale = decompose_matrix(obj["transform"])


def _read_group_light(obj, parent, id_):
    d = obj["data"]
    if d["type"] not in _LIGHT_TYPE_MAP:
        return

    light = bpy.data.lights.new(id_, _LIGHT_TYPE_MAP[d["type"]])
    light.color = (d["color"][0] / 255.0, d["color"][1] / 255.0, d["color"][2] / 255.0)
    light.distance = d["range"]
    light.contact_shadow_distance = d["shadowClipRange"]
    light.energy = d["intensity"] * 100.0
    light.use_shadow = d["bgShadowEnabled"] or d["characterShadowEnabled"]  # TODO: Separate these?

    light_obj = bpy.data.objects.new(id_, object_data=light)
    light_obj.location, light_obj.rotation_euler, light_obj.scale = decompose_matrix(obj["transform"])
    parent.objects.link(light_obj)


def read_kf_group(hash_, zf):
    name, json = open_json(hash_, zf)

    root = bpy.data.collections.new(name)

    for layer in json["layers"]:
        if len(layer["objects"]) < 1:
            continue
        if layer["props"]["festivalID"] > 0:
            continue

        group = bpy.data.collections.new(layer["props"]["name"])
        for k, v in layer["props"].items():
            group["KF_" + k] = v

        for child in layer["objects"]:
            if child["type"] == 1:
                _read_group_bg(child, zf, group)
            elif child["type"] == 3:
                _read_group_light(child, group, f"KF_L_{layer['props']['id']:08X}_{child['id']:08X}")
            elif child["type"] == 6 or child["type"] == 15:
                if "assetPath" not in child["data"]:
                    continue
                root_matrix = Matrix(child["transform"])
                group.children.link(
                    read_kf_shgroup(child["data"]["assetPath"], zf, root_matrix))

        root.children.link(group)

    return root
