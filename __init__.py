bl_info = {
    "name": "UVUnwrapGridAligner",
    "author": "ChatGPT",
    "version": (1, 7),
    "blender": (2, 80, 0),
    "location": "UV > Count UV Vertices",
    "description": "Counts, sorts, displays and spaces UV vertices (unique) in selected faces",
    "category": "UV",
}

import bpy
import bmesh
from bpy.types import Operator, Menu
from bpy.utils import register_class, unregister_class

class UV_OT_unwrap_grid_aligner(Operator):
    bl_idname = "uv.unwrap_grid_aligner"
    bl_label = "Distribute and Align Unwrapped UV Grid"
    bl_description = "Distribute UV vertices evenly along X and set Y to 0 (bottom) or 1 (top)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "Active object is not a mesh")
            return {'CANCELLED'}

        if context.mode != 'EDIT_MESH':
            self.report({'WARNING'}, "Must be in Edit Mode")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()

        top_map = {}
        bottom_map = {}

        for face in bm.faces:
            if not face.select:
                continue
            for loop in face.loops:
                luv = loop[uv_layer]
                if luv.select:
                    key = (round(luv.uv.x, 6), round(luv.uv.y, 6))
                    if luv.uv.y > 0.5:
                        top_map.setdefault(key, []).append(luv)
                    elif luv.uv.y < 0.5:
                        bottom_map.setdefault(key, []).append(luv)

        top_keys = sorted(top_map.keys())
        bottom_keys = sorted(bottom_map.keys())

        count = min(len(top_keys), len(bottom_keys))
        if count < 2:
            self.report({'WARNING'}, "Not enough vertex pairs to distribute.")
            return {'CANCELLED'}

        spacing = 1.0 / (count - 1)
        for i in range(count):
            x = i * spacing
            # Update all luvs at same (x, y) position
            for luv in top_map[top_keys[i]]:
                luv.uv.x = x
                luv.uv.y = 1.0
            for luv in bottom_map[bottom_keys[i]]:
                luv.uv.x = x
                luv.uv.y = 0.0

        bmesh.update_edit_mesh(obj.data)

        print(f"\n[UVUnwrapGridAligner] {count} columns aligned between X=0.0 and X=1.0 (with shared UVs)")
        self.report({'INFO'}, f"Aligned {count} UV columns with shared instances.")
        return {'FINISHED'}

class UV_MT_unwrap_grid_menu(Menu):
    bl_label = "Unwrap Grid Tools"
    bl_idname = "UV_MT_unwrap_grid_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator(UV_OT_unwrap_grid_aligner.bl_idname)

def draw_uv_menu(self, context):
    self.layout.menu(UV_MT_unwrap_grid_menu.bl_idname)

def register():
    register_class(UV_OT_unwrap_grid_aligner)
    register_class(UV_MT_unwrap_grid_menu)
    bpy.types.IMAGE_MT_uvs.append(draw_uv_menu)

def unregister():
    bpy.types.IMAGE_MT_uvs.remove(draw_uv_menu)
    unregister_class(UV_MT_unwrap_grid_menu)
    unregister_class(UV_OT_unwrap_grid_aligner)

if __name__ == "__main__":
    register()