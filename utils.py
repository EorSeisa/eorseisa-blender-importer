from struct import unpack, calcsize
from json import load
from mathutils import Euler, Quaternion, Matrix
from math import radians
from tempfile import NamedTemporaryFile

UINT_MAX = 0xFFFFFFFF


def read_struct(file, definition):
    buf = file.read(calcsize(definition))
    return unpack(definition, buf)


def open_hash(hash_, zf):
    info = zf.getinfo(f"XIV/{hash_:016X}")
    f = zf.open(info)
    return info.comment.decode(), f


def open_json(hash_, zf):
    name, f = open_hash(hash_, zf)
    ret = load(f)
    f.close()
    return name, ret


def to_temp(f, suffix=None, delete=True):
    f2 = NamedTemporaryFile(suffix=suffix, delete=delete)
    buf = f.read(8192)
    while len(buf) > 0:
        f2.write(buf)
        buf = f.read(8192)
    f2.flush()
    f2.seek(0)
    return f2


def decompose_transform(transform):
    t = transform["translate"]
    r = transform["rotate"]
    s = transform["scale"]
    return [
        (t[0], -t[2], t[1]),
        (r[0], -r[2], r[1]),
        (s[0], s[2], s[1])
    ]


def to_matrix(transform):
    rot = Euler((radians(transform[1][0]), radians(transform[1][1]), radians(transform[1][2])), "XYZ")
    return Matrix.LocRotScale(transform[0], rot, transform[2])


def decompose_matrix(transform):
    if type(transform) != Matrix:
        transform = Matrix(transform)
    loc, rot_q, scale = transform.decompose()
    rot = rot_q.to_euler('XYZ')
    ret = [
        (loc[0], -loc[2], loc[1]),
        (rot[0], -rot[2], rot[1]),
        (scale[0], scale[2], scale[1])
    ]
    return ret
