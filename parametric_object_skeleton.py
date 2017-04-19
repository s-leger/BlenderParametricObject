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


# ----------------------------------------------------------
# Blender Parametric object skeleton
# Author: Stephen Leger (s-leger)
# ----------------------------------------------------------

import bpy
import bmesh
from bpy.types import Operator, PropertyGroup, Object, Panel
from bpy.props import FloatProperty, IntProperty, CollectionProperty   

class BmeshEdit():  
    @staticmethod
    def _start(context, o):
        """
            private, start bmesh editing of active object
        """
        o.select = True
        context.scene.objects.active = o 
        bpy.ops.object.mode_set(mode='EDIT')    
        bm = bmesh.from_edit_mesh(o.data)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        return bm
        
    @staticmethod
    def _end(bm, o):   
        """
            private, end bmesh editing of active object
        """
        bmesh.update_edit_mesh(o.data, True)
        bpy.ops.object.mode_set(mode='OBJECT')
        bm.free()
        
    @staticmethod
    def _matids(bm, matids):
        """
            private, setup material ids
        """
        for i, matid in enumerate(matids):
            bm.faces[i].material_index = matid

    @staticmethod
    def _uvs(bm, uvs):
        """
            private, setup uv coords
        """
        layer = bm.loops.layers.uv.verify()
        l_i = len(uvs)
        for i, face in enumerate(bm.faces):
            for j, loop in enumerate(face.loops):
                loop[layer].uv = uvs[i][j]
    
    @staticmethod
    def buildmesh(context, o, verts, faces, matids=None, uvs=None, weld=False, clean=False):
        """
            public, build/update mesh on active object
            o : object
            verts: array of vertex 3d coords
            faces: array of faces verted indexes
            matids: array of material indexes for each face
            uvs: array of array of texture 2d coords for each face
        """
        bm = BmeshEdit._start(context, o)
        bm.clear()
        for v in verts:
            bm.verts.new(v)
        bm.verts.ensure_lookup_table()
        for f in faces:
            bm.faces.new([bm.verts[i] for i in f])
        bm.faces.ensure_lookup_table()
        if matids is not None:
            BmeshEdit._matids(bm, matids)
        if uvs is not None:
            BmeshEdit._uvs(bm, uvs)
        if weld:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        BmeshEdit._end(bm, o)
        if clean:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete_loose()
            bpy.ops.object.mode_set(mode='OBJECT')   
            
# ------------------------------------------------------------------
# Define property class to store object parameters and update mesh
# ------------------------------------------------------------------ 
def update(self, context):
    self.update(context)

class ParametricObjectProperty(PropertyGroup):
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
            (0,1,2,3),
            (7,6,5,4),
            (7,4,0,3),
            (4,5,1,0),
            (5,6,2,1),
            (6,7,3,2)
        ]

    @property
    def uvs(self):
        """
            Object faces uv coords
        """
        return  [
            [(0,0),(0,1),(1,1),(1,0)],
            [(0,0),(0,1),(1,1),(1,0)],
            [(0,0),(0,1),(1,1),(1,0)],
            [(0,0),(0,1),(1,1),(1,0)],
            [(0,0),(0,1),(1,1),(1,0)],
            [(0,0),(0,1),(1,1),(1,0)]
        ]

    @property
    def matids(self): 
        """
            Object material indexes
        """
        return [0,0,0,0,0,0]
        
    def update(self, context, topology=False):
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
        
    @classmethod
    def params(cls, o):
        if cls.filter(o):
            if o.data is not None and 'ParametricObjectProperty' in o.data:
                return o, o.data.ParametricObjectProperty[0]
        return o, None
        
    @classmethod
    def filter(cls, o):
        try:
            return bool(o.data is not None and 'ParametricObjectProperty' in o.data)
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
        m = bpy.data.meshes.new("ParametricObject")
        o = bpy.data.objects.new("ParametricObject", m)
        # attach parametric datablock
        d = o.data.ParametricObjectProperty.add()
        # update params
        d.x = self.x
        d.y = self.y
        d.z = self.z
        context.scene.link(o)
        # make newly created object active
        o.select = True
        context.scene.objects.active = o
        # create mesh data
        d.update(context, o)
        return o
    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------
    def execute(self, context):
        if context.mode == "OBJECT":
            bpy.ops.object.select_all(action="DESELECT")
            o = self.create(context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Option only valid in Object mode")
            return {'CANCELLED'}
        
def register(): 
    bpy.utils.register_class(ParametricObjectProperty)
    Mesh.ParametricObjectProperty = CollectionProperty(type=ParametricObjectProperty)
    bpy.utils.register_class(OBJECT_PT_parametric_object)
    bpy.utils.register_class(OBJECT_OT_parametric_object)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_parametric_object)
    bpy.utils.unregister_class(OBJECT_PT_parametric_object)
    bpy.utils.unregister_class(ParametricObjectProperty)
    del Mesh.ParametricObjectProperty

if __name__ == "__main__":
    register()
