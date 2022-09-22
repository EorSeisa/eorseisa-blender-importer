import bpy

from .utils import open_hash, read_struct


def read_kf_texture(hash_, zf):
    name, f = open_hash(hash_, zf)
    magic = f.read(4)
    if magic != b'KFT1':
        raise IOError(f"Invalid texture {hash_}")
    size, = read_struct(f, "Q")
    data = f.read(size)

    img = bpy.data.images.new(name, 8, 8)
    img.pack(data=data, data_len=size)
    img.source = "FILE"
    return img
