# -*- coding:utf-8 -*-

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# ----------------------------------------------------------
# Blender Parametric object skeleton
# Author: Stephen Leger (s-leger)
# ----------------------------------------------------------
bl_info = {
    'name': 'ParametricObject',
    'description': 'ParametricObject objects skeleton',
    'author': 's-leger',
    'license': 'GPL',
    'version': (1, 0, 0),
    'blender': (2, 7, 8),
    'location': 'View3D > Tools > Sample',
    'warning': '',
    'wiki_url': 'https://github.com/s-leger/BlenderParametricObject/wiki',
    'tracker_url': 'https://github.com/s-leger/BlenderParametricObject/issues',
    'link': 'https://github.com/s-leger/BlenderParametricObject',
    'support': 'COMMUNITY',
    'category': '3D View'
    }


import bpy
from bpy.types import Operator, PropertyGroup, Object, Panel
from bpy.props import FloatProperty, CollectionProperty
from .bmesh_utils import BmeshEdit
from .simple_manipulator import Manipulable


# ------------------------------------------------------------------
# Define property class to store object parameters and update mesh
# ------------------------------------------------------------------


def update(self, context):
    self.update(context)


class ParametricObjectProperty(Manipulable, PropertyGroup):

    x = FloatProperty(
            name='width',
            min=0.25, max=10000,
            default=100.0, precision=2,
            description='Width', update=update,
            )
    y = FloatProperty(
            name='depth',
            min=0.1, max=10000,
            default=0.80, precision=2,
            description='Depth', update=update,
            )
    z = FloatProperty(
            name='height',
            min=0.1, max=10000,
            default=2.0, precision=2,
            description='Height', update=update,
            )

    @property
    def verts(self):
        """
            Object vertices coords
        """
        x = self.x
        y = self.y
        z = self.z
        return [
            (0, y, 0),
            (0, 0, 0),
            (x, 0, 0),
            (x, y, 0),
            (0, y, z),
            (0, 0, z),
            (x, 0, z),
            (x, y, z)
        ]

    @property
    def faces(self):
        """
            Object faces vertices index
        """
        return [
            (0, 1, 2, 3),
            (7, 6, 5, 4),
            (7, 4, 0, 3),
            (4, 5, 1, 0),
            (5, 6, 2, 1),
            (6, 7, 3, 2)
        ]

    @property
    def uvs(self):
        """
            Object faces uv coords
        """
        return [
            [(0, 0), (0, 1), (1, 1), (1, 0)],
            [(0, 0), (0, 1), (1, 1), (1, 0)],
            [(0, 0), (0, 1), (1, 1), (1, 0)],
            [(0, 0), (0, 1), (1, 1), (1, 0)],
            [(0, 0), (0, 1), (1, 1), (1, 0)],
            [(0, 0), (0, 1), (1, 1), (1, 0)]
        ]

    @property
    def matids(self):
        """
            Object material indexes
        """
        return [0, 0, 0, 0, 0, 0]

    def update(self, context):

        old = context.active_object

        o, props = OBJECT_PT_parametric_object.params(old)
        if props != self:
            return

        o.select = True
        context.scene.objects.active = o

        BmeshEdit.buildmesh(context, o, self.verts, self.faces, matids=self.matids, uvs=self.uvs)

        # restore context
        old.select = True
        context.scene.objects.active = old

# ------------------------------------------------------------------
# Define panel class to show object parameters in ui panel (N)
# ------------------------------------------------------------------


class OBJECT_PT_parametric_object(Panel):
    bl_idname = "OBJECT_PT_parametric_object"
    bl_label = "Parametric"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sample'

    def draw(self, context):
        layout = self.layout
        o = context.object
        o, props = OBJECT_PT_parametric_object.params(o)
        if props is None:
            return
        layout.prop(props, 'x')
        layout.prop(props, 'y')
        layout.prop(props, 'z')
        layout.operator("object.parametric_object_manipulate")

    @classmethod
    def params(cls, o):
        if cls.filter(o):
            if 'ParametricObjectProperty' in o:
                return o, o.ParametricObjectProperty[0]
            else:
                for child in o.children:
                    o, props = cls.params(child)
                    if props is not None:
                        return o, props
        return o, None

    @classmethod
    def filter(cls, o):
        try:
            return bool('ParametricObjectProperty' in o)
        except:
            return False

    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        return cls.filter(o)

# ------------------------------------------------------------------
# Define operator class to create object
# ------------------------------------------------------------------


class OBJECT_OT_parametric_object(Operator):
    bl_idname = "object.parametric_object"
    bl_label = "Parametric"
    bl_description = "Create simple parametric object"
    bl_category = 'Sample'
    bl_options = {'REGISTER', 'UNDO'}

    x = FloatProperty(
            name='width',
            min=0.1, max=10000,
            default=0.80, precision=2,
            description='Width'
            )
    y = FloatProperty(
            name='depth',
            min=0.1, max=10000,
            default=0.80, precision=2,
            description='Depth'
            )
    z = FloatProperty(
            name='height',
            min=0.1, max=10000,
            default=2.0, precision=2,
            description='height'
            )

    def create(self, context):
        """
            expose only basic params in operator
            use object property for other params
        """
        m = bpy.data.meshes.new("Parametric Object")
        o = bpy.data.objects.new("Parametric Object", m)
        # attach parametric datablock
        d = o.ParametricObjectProperty.add()
        # update params
        d.x = self.x
        d.y = self.y
        d.z = self.z
        context.scene.link(o)
        # make newly created object active
        o.select = True
        context.scene.objects.active = o
        # create mesh data
        d.update(context)

        # setup manipulators for on screen editing
        h = m.manipulators.add()
        h.prop1_name = "x"
        h = m.manipulators.add()
        h.prop1_name = "y"
        h = m.manipulators.add()
        h.prop1_name = "z"

        return o

    def execute(self, context):
        if context.mode == "OBJECT":
            bpy.ops.object.select_all(action="DESELECT")
            o = self.create(context)
            o.location = context.scene.cursor_location
            # activate manipulators at creation time
            bpy.ops.object.parametric_object_manipulate()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Option only valid in Object mode")
            return {'CANCELLED'}

# ------------------------------------------------------------------
# Define operator class to manipulate object
# ------------------------------------------------------------------


class OBJECT_OT_parametric_object_manipulate(Operator):
    bl_idname = "object.parametric_object_manipulate"
    bl_label = "Manipulate"
    bl_description = "Manipulate"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return OBJECT_PT_parametric_object.filter(context.active_object)

    def modal(self, context, event):
        return self.d.manipulable_modal(context, event)

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            o = context.active_object
            self.d = o.data.ParametricObjectProperty[0]
            self.d.manipulable_invoke(context)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(ParametricObjectProperty)
    Object.ParametricObjectProperty = CollectionProperty(type=ParametricObjectProperty)
    bpy.utils.register_class(OBJECT_PT_parametric_object)
    bpy.utils.register_class(OBJECT_OT_parametric_object)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_parametric_object)
    bpy.utils.unregister_class(OBJECT_PT_parametric_object)
    bpy.utils.unregister_class(ParametricObjectProperty)
    del Object.ParametricObjectProperty


if __name__ == "__main__":
    register()
