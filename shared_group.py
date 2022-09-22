import bpy

from json import load
from mathutils import Matrix

from .utils import to_matrix, open_hash, decompose_matrix
from .model import read_kf_model


def _combine_transforms(a, b):
    if b is None:
        return a
    mat_a = to_matrix(a)
    mat_b = to_matrix(b)
    mat = mat_b @ mat_a
    loc, rot, scale = mat.decompose()
    return [loc, rot.to_euler("XYZ"), scale]


def _read_shgroup_model(obj, zf, parent, pre=Matrix()):
    if "asset" not in obj["data"]:
        return
    mdl = read_kf_model(obj["data"]["asset"], zf, parent)
    mdl_transform = Matrix(obj["transform"])
    mdl.location, mdl.rotation_euler, mdl.scale = decompose_matrix(pre @ mdl_transform)


def read_kf_shgroup(hash_, zf, pre=Matrix()):
    name, f = open_hash(hash_, zf)
    json = load(f)

    root = bpy.data.collections.new(name)

    for k, v in json["props"].items():
        root["KF_" + k] = v

    for entry in json["entries"]:
        if entry["type"] == 1:
            _read_shgroup_model(entry, zf, root, pre)
        if entry["type"] == 6:
            if "asset" not in entry["data"]:
                continue
            new_transform = pre @ Matrix(entry["transform"])
            root.children.link(read_kf_shgroup(entry["data"]["asset"], zf, new_transform))

    return root
