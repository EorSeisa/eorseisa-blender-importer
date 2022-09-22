import bpy

from json import load

from .utils import get_path
from .terrain import read_kf_terrain
from .group import read_kf_group

_EXT_MAP = {
    "terrain": "kftera",
    "lgb": "kflgb",
}


def read_kf_scene(filename):
    with open(filename) as f:
        data = load(f)

    dir_ = data["cacheDir"]
    root = bpy.data.collections.new(data["name"])

    for item in data["items"]:
        type_ = item["type"]
        if type_ not in _EXT_MAP:
            continue
        path = get_path(dir_, item["id"], _EXT_MAP[type_])
        if type_ == "terrain":
            ret = read_kf_terrain(path)
            root.children.link(ret)
        elif type_ == "lgb":
            ret = read_kf_group(path, root)
            root.children.link(ret)
        else:
            print(f"WARN: UNSUPPORTED TYPE {item['type']}")

    return root
