This is minimal value product of Langerie Generator.

THis is only including Pants in one color.
But an algorithm of generating mesh is great.
You should think this as MVP.
You should add bone, material,. weight, bra, and all other things to be needed for VRChat langerie.
Do not use hard coding and magic numbers.
色も選べるべきだ。

```py
import bpy
import bmesh

# --- プロパティ ---
class UnderwearProps(bpy.types.PropertyGroup):
    base_body: bpy.props.PointerProperty(
        name="素体",
        type=bpy.types.Object,
        description="下着を生成する素体"
    )

# --- パネル ---
class UNDERWEAR_PT_Main(bpy.types.Panel):
    bl_label = "ミニマル下着生成"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "下着"

    def draw(self, context):
        props = context.scene.underwear_props
        layout = self.layout
        layout.prop_search(props, "base_body", bpy.data, "objects", text="素体")
        layout.operator("underwear.generate", text="パンツ生成")

# --- パンツ生成 ---
def create_pants_mesh(base_obj):
    # 頂点グループ「hip」検索
    vg = None
    for group in base_obj.vertex_groups:
        if "hip" in group.name.lower() or "腰" in group.name:
            vg = group
            break
    if vg is None:
        return None

    mesh = base_obj.data.copy()
    obj = bpy.data.objects.new(base_obj.name + "_pants", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    deform = bm.verts.layers.deform.verify()
    # hipグループのウェイトが高い頂点だけ残す
    selected = [v for v in bm.verts if vg.index in v[deform] and v[deform][vg.index] > 0.5]
    remove = [v for v in bm.verts if v not in selected]
    bmesh.ops.delete(bm, geom=remove, context='VERTS')
    # 軽く押し出し
    for v in bm.verts:
        v.co += v.normal * 0.01
    bm.to_mesh(mesh)
    bm.free()

    # スムーズ
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    return obj

# --- マテリアル生成（Blender 4.1対応）---
def create_lavender_material():
    mat = bpy.data.materials.new("Lavender_Trans")
    mat.use_nodes = True
    mat.blend_method = 'BLEND'
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in nodes: nodes.remove(n)
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    out.location = (200,0)
    bsdf.location = (0,0)
    # ラベンダー色＋半透明
    bsdf.inputs["Base Color"].default_value = (0.7, 0.5, 1.0, 1.0)
    bsdf.inputs["Alpha"].default_value = 0.4
    # Blender 4.x対応: Specular or Specular IOR Level
    if "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.5
    elif "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.5
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

# --- オペレーター ---
class UNDERWEAR_OT_Generate(bpy.types.Operator):
    bl_idname = "underwear.generate"
    bl_label = "パンツ生成"
    def execute(self, context):
        props = context.scene.underwear_props
        base_obj = props.base_body
        if not base_obj or base_obj.type != 'MESH':
            self.report({'ERROR'}, "有効な素体を選択してください")
            return {'CANCELLED'}
        pants = create_pants_mesh(base_obj)
        if not pants:
            self.report({'ERROR'}, "hip頂点グループが見つかりません")
            return {'CANCELLED'}
        mat = create_lavender_material()
        pants.data.materials.clear()
        pants.data.materials.append(mat)
        self.report({'INFO'}, "パンツ生成完了")
        return {'FINISHED'}

# --- 登録 ---
classes = [UnderwearProps, UNDERWEAR_PT_Main, UNDERWEAR_OT_Generate]
def register():
    for c in classes: bpy.utils.register_class(c)
    bpy.types.Scene.underwear_props = bpy.props.PointerProperty(type=UnderwearProps)
def unregister():
    for c in reversed(classes): bpy.utils.unregister_class(c)
    del bpy.types.Scene.underwear_props
if __name__ == "__main__":
    register()
```