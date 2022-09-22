import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from json import load as json_load
from os import path
from zipfile import ZipFile

from .terrain import read_kf_terrain
from .utils import read_struct
from .group import read_kf_group

bl_info = {
    "name": "EorSeisa Importer",
    "category": "Import-Export",
    "version": (0, 0, 1),
    "blender": (3, 0, 0),
    "location": "File > Import > EorSeisa",
    "description": "Import EorSeisa scene files",
    "isDraft": False,
    "developer": "じゅりない",
    "url": "https://eorseisa.alt.icu",
}


def read_eorseisa_file(context, filepath, use_some_setting):
    with ZipFile(filepath) as zf:
        _, ext = path.splitext(filepath)

        with zf.open("INDEX.json") as f:
            index_data = json_load(f)

        if index_data["meta"]["version"] != 1:
            raise IOError("Unknown KF archive version")

        for obj in index_data["objects"]:
            if obj["type"] == 1:
                bpy.context.scene.collection.children.link(read_kf_terrain(obj["id"], zf))
            elif obj["type"] == 2:
                bpy.context.scene.collection.children.link(read_kf_group(obj["id"], zf))

    return {"FINISHED"}


class ImportSomeData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "eorseisa_importer.import_model"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import EorSeisa Scene"

    # ImportHelper mixin class uses this
    filename_ext = ".kf"

    filter_glob: StringProperty(
        default="*.kf",
        options={"HIDDEN"},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )

    type: EnumProperty(
        name="Example Enum",
        description="Choose between two items",
        items=(
            ("OPT_A", "First Option", "Description one"),
            ("OPT_B", "Second Option", "Description two"),
        ),
        default="OPT_A",
    )

    def execute(self, context):
        return read_eorseisa_file(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu.
def menu_func_import(self, context):
    self.layout.operator(ImportSomeData.bl_idname, text="EorSeisa (.kf)")


# Register and add to the "file selector" menu (required to use F3 search "Text Import Operator" for quick access).
def register():
    bpy.utils.register_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
