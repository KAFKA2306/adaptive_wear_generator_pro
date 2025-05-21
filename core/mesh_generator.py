import bpy
from bpy.props import BoolProperty, FloatProperty

def get_vertex_group_names(body_obj):
    """メッシュから頂点グループ名のリストを取得する"""
    return [vg.name for vg in body_obj.vertex_groups]
def find_vertex_group_by_keyword(body_obj, keywords):
    """キーワードで頂点グループをフィルタリング"""
    found = []
    for vg in body_obj.vertex_groups:
        for kw in keywords:
            if kw.lower() in vg.name.lower():
                found.append(vg.name)
                break
    return found
def create_basic_garment_mesh(body_obj):
    """基本的なガーメントメッシュを作成"""
    mesh_data = bpy.data.meshes.new("mvp_garment_mesh")
    garment_obj = bpy.data.objects.new("MVP_Garment", mesh_data)
    bpy.context.collection.objects.link(garment_obj)
    return garment_obj

def create_underwear_pants_mesh(body_obj, vg_names):
    """パンツ形状のメッシュを生成"""
    mesh_data = bpy.data.meshes.new("mvp_underwear_pants_mesh")
    pants_obj = bpy.data.objects.new("MVP_Pants", mesh_data)
    bpy.context.collection.objects.link(pants_obj)
    return pants_obj

def create_underwear_bra_mesh(body_obj, vg_names):
    """ブラジャー形状のメッシュを生成"""
    mesh_data = bpy.data.meshes.new("mvp_underwear_bra_mesh")
    bra_obj = bpy.data.objects.new("MVP_Bra", mesh_data)
    bpy.context.collection.objects.link(bra_obj)
    return bra_obj
def create_socks_mesh(body_obj, vg_names, length="ankle"):
    """靴下メッシュを生成（長さ指定可能）"""
    mesh_data = bpy.data.meshes.new(f"mvp_socks_{length}_mesh")
    socks_obj = bpy.data.objects.new(f"MVP_Socks_{length}", mesh_data)
    bpy.context.collection.objects.link(socks_obj)
    return socks_obj
def check_polygon_count(obj, max_count=10000):
    """メッシュのポリゴン数が上限以下かチェック"""
    if obj and obj.type == 'MESH':
        poly_count = len(obj.data.polygons)
        return poly_count <= max_count
    return True
class AWGP_OT_GenerateGarment(bpy.types.Operator):
    bl_idname = "awgp.generate_garment"
    bl_label = "Generate Garment"
    bl_description = "素体に基づき衣装を自動生成"
    bl_options = {'REGISTER', 'UNDO'}

    fit_tightly: BoolProperty(
        name="Tight Fit",
        description="体に密着するフィット感にする",
        default=True
    )

    thickness: FloatProperty(
        name="Thickness",
        description="衣装の厚み (mm)",
        default=2.0,
        min=0.1,
        max=10.0
    )

    def execute(self, context):
        body = context.active_object
        if not body or body.type != 'MESH':
            self.report({'ERROR'}, "メッシュオブジェクトを選択してください")
            return {'CANCELLED'}

        from .mesh_generator import create_basic_garment_mesh
        garment = create_basic_garment_mesh(body)

        if garment:
            from .fit_engine import fit_mesh_to_body
            fit_mesh_to_body(garment, body,
                            offset=0.001 if self.fit_tightly else 0.01,
                            thickness=self.thickness/1000)

            from .uv_tools import unwrap_uv
            unwrap_uv(garment)

            from .material_manager import apply_basic_material
            apply_basic_material(garment)

            self.report({'INFO'}, "衣装が生成されました")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "衣装の生成に失敗しました")
            return {'CANCELLED'}
