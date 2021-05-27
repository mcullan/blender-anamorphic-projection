#EXECUTE
import bpy
import numpy as np
from mathutils import Vector, Matrix
import bpy

bl_info = {
    "name": "Anamorphic Projection",
    "author": "Michael Cullan",
    "description": 
    """
Creates an anamorphic projection between two cameras, or with a single camera and a horizontal/vertical shift in view space.
In other words, this modifies an object (or a duplicate of an object) to match the current perspective view, but from another viewpoint. 
Can be used to create optical illusions. 
    """,
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "View3D",
    "warning": "",
    "category": "Object"
}

def copy_object(obj, linked=False):
    """Create a copy of obj. Unlinked by default."""

    dupe = obj.copy()
    if (not linked) and obj.data:
        dupe.data = dupe.data.copy()
    
    col = obj.users_collection[0]

    col.objects.link(dupe)

    return dupe.name


def get_cameras(scene, context):
    """Get the names of all CAMERA objects in the current environment. """
 
    objects = bpy.data.objects
    camera_names = [ob for ob in objects if ob.type == 'CAMERA']
    enum_items = [(ob.name, ob.name, "") for x, ob in enumerate(camera_names)]

    return enum_items


def project_anamorphic(ob, from_camera, to_camera, x_translate, y_translate, render):
    """Project from one perspective camera to another."""
          
    if from_camera.type != 'CAMERA':
        raise Exception("Object {} is not a camera.".format(camera.name))

    if to_camera.type != 'CAMERA':
        raise Exception("Object {} is not a camera.".format(camera.name))

    modelview_matrix = from_camera.matrix_world.inverted()
    modelview_matrix_end = to_camera.matrix_world.inverted()
    
    res_x_copy = bpy.context.scene.render.resolution_x
    res_y_copy = bpy.context.scene.render.resolution_y
    
    """For some reason, seems to work only when aspect ratio is 4:3, probably because of shape of camera sensor?"""
    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 900

    depsgraph = bpy.data.scenes["Scene"].view_layers["View Layer"].depsgraph

    projection_matrix = from_camera.calc_matrix_camera(
        depsgraph,
        x = render.resolution_x,
        y = render.resolution_y,
        scale_x = render.pixel_aspect_x,
        scale_y = render.pixel_aspect_y)

    projection_matrix_end = to_camera.calc_matrix_camera(
        depsgraph,
        x = render.resolution_x,
        y = render.resolution_y,
        scale_x = render.pixel_aspect_x,
        scale_y = render.pixel_aspect_y)

    length = len(ob.data.vertices)
    verts_co = np.zeros(length * 3)
    ob.data.vertices.foreach_get('co', verts_co)
    verts_co.shape = (length, 3)
    verts_co_4d = np.ones(shape=(length, 4), dtype=np.float)
    verts_co_4d[:, :-1] = verts_co

    matrix_world = np.array(ob.matrix_world)
    matrix_world_inv = np.array(ob.matrix_world.inverted())
        
    vertex_matrix = (matrix_world @ verts_co_4d.T)

    # tmatrix = np.array( (projection_matrix_end @ modelview_matrix_end).inverted() @ projection_matrix @ modelview_matrix)
    out_p = np.array(projection_matrix @ modelview_matrix) @ vertex_matrix
    
    out_p [:3, :] = out_p[:3, :] / out_p[3, :]
    out_p[0,: ] += x_translate
    out_p[1, :] += y_translate
    out_p[:3, :] = out_p[:3, :] *  out_p[3, :]

    to_coordinates = (np.array( matrix_world_inv @ (projection_matrix_end @ modelview_matrix_end).inverted() ) @ out_p).T

    ob.data.vertices.foreach_set('co', to_coordinates[:, :3].reshape(-1, ))

    bpy.context.scene.render.resolution_x = res_x_copy
    bpy.context.scene.render.resolution_y = res_y_copy
    
    return


def project_point_ortho(from_camera: bpy.types.Object,
                        to_camera: bpy.types.Object,
                        p: Vector,
                        depth_multiplier:float,
                        render) -> Vector:
    """Project a single point to perspective screen space, then back to 3D to match the view of an orthographic camera."""

    if from_camera.type != 'CAMERA':
        raise Exception("Object {} is not a camera.".format(from_camera.name))
    if to_camera.type != 'CAMERA':
        raise Exception("Object {} is not a camera.".format(to_camera.name))

    if from_camera.data.type != 'PERSP':
            raise Exception(" {} is not in Orthographic mode.".format(camera.name))

    if to_camera.data.type != 'ORTHO':
        raise Exception(" {} is not in Orthographic mode.".format(camera.name))

    if len(p) != 3:
        raise Exception("Vector {} is not three-dimensional".format(p))

    ortho_scale = bpy.data.objects[to_camera.name].data.ortho_scale
    
    # For some reason, seems to work only when aspect ratio is 4:3, probably because of shape of camera sensor?
    # So we set the resolution to 1200x900, then set it back to the original resolution at the end of this function.
    res_x_copy = bpy.context.scene.render.resolution_x
    res_y_copy = bpy.context.scene.render.resolution_y
    
    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 900
    
    modelview_matrix_from = from_camera.matrix_world.inverted()
    projection_matrix_from = from_camera.calc_matrix_camera(
        bpy.data.scenes["Scene"].view_layers["View Layer"].depsgraph,
        x = render.resolution_x,
        y = render.resolution_y,
        scale_x = render.pixel_aspect_x,
        scale_y = render.pixel_aspect_y)

    modelview_matrix_to = to_camera.matrix_world
    projection_matrix_to = to_camera.calc_matrix_camera(
        bpy.data.scenes["Scene"].view_layers["View Layer"].depsgraph,
        x = render.resolution_x,
        y = render.resolution_y,
        scale_x = render.pixel_aspect_x,
        scale_y = render.pixel_aspect_y)


    # Project to screen space
    p1 = (projection_matrix_from @ modelview_matrix_from) @ Vector((p.x, p.y, p.z, 1))
    
    ratio = render.resolution_x / render.resolution_y

    w = p1.w
    z3 = -p1.z * depth_multiplier
    
    # Create orthographic 3D vector
    p3 = Vector((((p1.x / (w / ratio)), (p1.y / w) , z3 )))
    
    # Transform to align with to_camera view 
    # Multiply by 2.6666 because it expects the screen space to be (-1, 1) but somehow the 4/3 ratio factors in here
    p4 = (modelview_matrix_to @ (p3 * (2.666666 )))

    bpy.context.scene.render.resolution_x = res_x_copy
    bpy.context.scene.render.resolution_y = res_y_copy

    return p4


def project_anamorphic_ortho(ob, from_camera, to_camera,  depth_multiplier=1, render=None,):
    """Project an entire mesh into screen space, then back to 3D as seen by an orthographic camera"""
    modelview_matrix = from_camera.matrix_world.inverted()
    ortho_matrix = to_camera.matrix_world.inverted()
    
    for p in ob.data.vertices:
        
        co = ob.matrix_world @ p.co
        proj_p = project_point_ortho(from_camera=from_camera, to_camera=to_camera, p=co, depth_multiplier=depth_multiplier, render=render)
        p.co =  (ob.matrix_world.inverted() @ proj_p )


class AnamorphicProperties(bpy.types.PropertyGroup):

    # Used in project_anamorphic
    x_translate : bpy.props.FloatProperty(
        name="X translate",
        default=0,
        soft_min=-1,
        soft_max=1,
        step=10,
        description="Horizontal screen space translation, where the screen ranges from (-1,1). Used only when to_camera is pesrpective.")

    # Used in project_anamorphic
    y_translate : bpy.props.FloatProperty(
        name="Y translate",
        default=0,
        soft_min=-1,
        soft_max=1,
        step=10,
        description="Vertical screen space translation, where the screen ranges from (-1,1). Used only when to_camera is pesrpective.")

    # Used in project_anamorphic_ortho
    depth_multiplier : bpy.props.FloatProperty(
        name="Depth Multiplier",
        default=1,
        soft_min=-10,
        soft_max=10,
        step=10,
        description="Only used when to_camera is orthographic. Increase/decrease the depth of the projection.")

    # Used in all projection functions
    from_camera_enum : bpy.props.EnumProperty(
            name="From",
            description="Projection will match this camera's view",
            items=get_cameras
    )

    # Used in all projection functions
    to_camera_enum : bpy.props.EnumProperty(
            name="To",
            description="Projection will be viewed through this camera",
            items=get_cameras
    )



class Anamorphic_PT_main_panel(bpy.types.Panel):
    bl_label = "Anamorphic Projection"
    bl_idname = "Anamorphic_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Anamorphic Projection"

    @classmethod
    def poll(self, context):
        """Should only appear if the current object is a mesh, since it operates on vertices"""
        obj = context.object
        if obj is not None:
            if obj.type == "MESH" and obj.mode == "OBJECT":
                return True

        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool


        layout.prop(mytool, "from_camera_enum")
        layout.prop(mytool, "to_camera_enum")
        row = layout.row()
        row.separator()

        layout.prop(mytool, "x_translate")
        layout.prop(mytool, "y_translate")
        row = layout.row()
        row.separator()

        row = layout.row()
        layout.prop(mytool, "depth_multiplier")

        row = layout.row()
        col = layout.column()
        row.operator("anamorphic.anamorphic_modify")
        row.operator("anamorphic.anamorphic_copy")



class Anamorphic_OT_Modify(bpy.types.Operator):
    """Calls project_anamorphic or project_anamorphic ortho on the current object."""
    bl_label = "Modify Active"
    bl_idname = "anamorphic.anamorphic_modify"
    bl_description = "Apply projection on the active object."
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        render = scene.render
        mytool = scene.my_tool

        from_camera = bpy.data.objects[mytool.from_camera_enum]
        to_camera = bpy.data.objects[mytool.to_camera_enum]

        if to_camera.data.type == "PERSP":
            project_anamorphic(
                bpy.context.object,
                from_camera,
                to_camera,
                mytool.x_translate,
                mytool.y_translate,
                render
                )     
        elif to_camera.data.type == "ORTHO":
            project_anamorphic_ortho(
                bpy.context.object,
                from_camera,
                to_camera,
                mytool.depth_multiplier,
                render
                ) 
        else:
            raise ValueError("Object to_camera cannot be Panoramic.")   

        obj = bpy.context.object
        obj.select_set(True)
        bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS")
        return {"FINISHED"}

class Anamorphic_OT_Copy(bpy.types.Operator):
    """Calls project_anamorphic or project_anamorphic ortho on a copy of the current object."""
    bl_label = "Modify Copy"
    bl_idname = "anamorphic.anamorphic_copy"
    bl_description = "Apply projection on a copy of the active object."
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        render = scene.render
        mytool = scene.my_tool

        from_camera = bpy.data.objects[mytool.from_camera_enum]
        to_camera = bpy.data.objects[mytool.to_camera_enum]
        x_translate = mytool.x_translate



        dupe_name = copy_object(bpy.context.object, linked=False)
        dupe = bpy.data.objects[dupe_name]
        dupe.select_set(True)

        if to_camera.data.type == "PERSP":
            project_anamorphic(
                dupe,
                from_camera,
                to_camera,
                mytool.x_translate,
                mytool.y_translate,
                render
                )     
        elif to_camera.data.type == "ORTHO":
            project_anamorphic_ortho(
                dupe,
                from_camera,
                to_camera,
                mytool.depth_multiplier,
                render
                ) 
        else:
            raise ValueError("Object to_camera cannot be Panoramic.")


        bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS")
        return {"FINISHED"}



classes = (AnamorphicProperties, Anamorphic_PT_main_panel, Anamorphic_OT_Modify, Anamorphic_OT_Copy)


def register():
    for c in classes:
        bpy.utils.register_class(c)

        bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=AnamorphicProperties)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    del bpy.types.Scene.my_tool



