import bpy
from bpy.props import StringProperty

# Import necessary functions from other modules
from .mesh_generator import find_vertex_group_by_keyword, create_underwear_pants_mesh, create_underwear_bra_mesh
from .fit_engine import fit_mesh_to_body
from .uv_tools import unwrap_uv
from .material_manager import apply_basic_material, create_lavender_material

class AWGP_OT_GenerateWear(bpy.types.Operator):
    bl_idname = "awgp.generate_wear"
    bl_label = "衣装生成"
    bl_description = "素体に基づき選択した衣装を自動生成"
    bl_options = {'REGISTER', 'UNDO'}

    garment_type: StringProperty()
    fit_tightly: bpy.props.BoolProperty()
    thickness: bpy.props.FloatProperty()

    def execute(self, context):
        body = context.active_object
        if not body or body.type != 'MESH':
            self.report({'ERROR'}, "メッシュオブジェクトを選択してください")
            return {'CANCELLED'}

        garment = None
        # vg_names = [] # Vertex group names might be needed for other types

        # Log received properties for verification
        print(f"Generating garment type: {self.garment_type}")
        print(f"Fit tightly: {self.fit_tightly}")
        print(f"Thickness: {self.thickness}")

        # Dispatch based on garment_type
        if self.garment_type == 'pants':
            vg_candidates = find_vertex_group_by_keyword(body, ["thigh", "leg"])
            if not vg_candidates:
                self.report({'ERROR'}, "「thigh」または「leg」を含む頂点グループが見つかりません")
                return {'CANCELLED'}
            garment = create_underwear_pants_mesh(body, vg_candidates, self.fit_tightly, self.thickness)
        elif self.garment_type == 'bra':
            # Need to get relevant vertex groups for bra
            vg_candidates = find_vertex_group_by_keyword(body, ["chest", "breast"])
            if not vg_candidates:
                self.report({'ERROR'}, "「chest」または「breast」を含む頂点グループが見つれません")
                return {'CANCELLED'}
            garment = create_underwear_bra_mesh(body, vg_candidates, self.fit_tightly, self.thickness)
        elif self.garment_type == 'socks':
            # Need to get relevant vertex groups for socks
            vg_candidates = find_vertex_group_by_keyword(body, ["foot", "leg"])
            if not vg_candidates:
                self.report({'ERROR'}, "「foot」または「leg」を含む頂点グループが見つかりません")
                return {'CANCELLED'}
            # Note: length parameter needs to be added to the operator later
            garment = create_socks_mesh(body, vg_candidates, self.fit_tightly, self.thickness)
        elif self.garment_type == 'gloves':
            # Need to get relevant vertex groups for gloves
            vg_candidates = find_vertex_group_by_keyword(body, ["hand", "arm"])
            if not vg_candidates:
                self.report({'ERROR'}, "「hand」または「arm」を含む頂点グループが見つかりません")
                return {'CANCELLED'}
            # Note: fingered parameter needs to be added to the operator later
            garment = create_gloves_mesh(body, vg_candidates, self.fit_tightly, self.thickness)
        elif self.garment_type == 'onesie':
            # Need to get relevant vertex groups for onesie
            vg_candidates = find_vertex_group_by_keyword(body, ["torso", "body"])
            if not vg_candidates:
                self.report({'ERROR'}, "「torso」または「body」を含む頂点グループが見つかりません")
                return {'CANCELLED'}
            garment = create_swimsuit_onesie_mesh(body, vg_candidates, self.fit_tightly, self.thickness)
        elif self.garment_type == 'bikini':
            # Need to get relevant vertex groups for bikini
            vg_candidates = find_vertex_group_by_keyword(body, ["chest", "breast", "pelvis"])
            if not vg_candidates:
                self.report({'ERROR'}, "「chest」、「breast」または「pelvis」を含む頂点グループが見つかりません")
                return {'CANCELLED'}
            garment = create_swimsuit_bikini_mesh(body, vg_candidates, self.fit_tightly, self.thickness)
        elif self.garment_type == 'tights':
            # Need to get relevant vertex groups for tights
            vg_candidates = find_vertex_group_by_keyword(body, ["leg", "pelvis"])
            if not vg_candidates:
                self.report({'ERROR'}, "「leg」または「pelvis」を含む頂点グループが見つかりません")
                return {'CANCELLED'}
            # Note: opacity and length parameters need to be added to the operator later
            garment = create_tights_mesh(body, vg_candidates, self.fit_tightly, self.thickness)


        if garment:
            # Integrate core flow steps
            # Note: Arguments for fit_mesh_to_body, unwrap_uv, apply_basic_material need to be finalized based on later tasks
            fit_mesh_to_body(garment, body)
            unwrap_uv(garment)
            apply_basic_material(garment)

            self.report({'INFO'}, f"{self.garment_type} が生成されました")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"{self.garment_type} の生成に失敗しました")
            return {'CANCELLED'}

# --- オペレーター ---
class UNDERWEAR_OT_Generate(bpy.types.Operator):
    bl_idname = "underwear.generate"
    bl_label = "パンツ生成"
    bl_options = {'REGISTER', 'UNDO'} # オプションを追加

    def execute(self, context):
        props = context.scene.underwear_props
        base_obj = props.base_body

        if not base_obj or base_obj.type != 'MESH':
            self.report({'ERROR'}, "有効な素体を選択してください")
            return {'CANCELLED'}

        # create_underwear_pants_mesh は頂点グループ検索も内部で行う
        # 既存の関数シグネチャに合わせるため、vg_namesは空リストで渡す
        pants = create_underwear_pants_mesh(base_obj, [])

        if not pants:
            self.report({'ERROR'}, "hip頂点グループが見つからないか、メッシュ生成に失敗しました")
            return {'CANCELLED'}

        mat = create_lavender_material()
        if mat: # マテリアルが正常に作成されたかチェック
            pants.data.materials.clear()
            pants.data.materials.append(mat)

        self.report({'INFO'}, "パンツ生成完了")
        return {'FINISHED'}