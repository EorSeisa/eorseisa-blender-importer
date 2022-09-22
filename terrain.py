import bpy

from .utils import read_struct, open_json
from .model import read_kf_model


def read_kf_terrain(uid, zf):
    name, json = open_json(uid, zf)
    col = bpy.data.collections.new(name)

    for plate in json["plates"]:
        model = read_kf_model(plate["asset"], zf, col)
        model.location = (plate["position"][0], -plate["position"][1], 0)

    return col
