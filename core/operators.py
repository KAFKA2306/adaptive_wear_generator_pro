import bpy
import json # JSONモジュールをインポート
from bpy.props import StringProperty
from adaptive_wear_generator_pro.services.logging_service import log_info # logging_service をインポート

# Import necessary functions from other modules
# Import necessary functions from other modules
# (プレースホルダー関数をインポート)
from adaptive_wear_generator_pro.core.mesh_generator import generate_initial_wear_mesh # 仮のインポート
from adaptive_wear_generator_pro.core.fit_engine import fit_wear_to_body # 仮のインポート

# 既存のインポート (必要に応じて維持または整理)
from adaptive_wear_generator_pro.core.mesh_generator import find_vertex_group_by_keyword, create_underwear_pants_mesh, create_underwear_bra_mesh, create_socks_mesh, create_gloves_mesh, create_swimsuit_onesie_mesh, create_swimsuit_bikini_mesh, create_tights_mesh
# from .fit_engine import fit_mesh_to_body # fit_wear_to_body に置き換えられるためコメントアウトまたは削除
from adaptive_wear_generator_pro.core.uv_tools import unwrap_uv
from adaptive_wear_generator_pro.core.material_manager import apply_basic_material, create_lavender_material


class AWG_OT_GenerateWear(bpy.types.Operator): # クラス名を修正
    bl_idname = "awg.generate_wear" # 指示通りに修正
    bl_label = "Generate Wear" # 指示通りに修正
    bl_description = "選択された設定に基づいて衣装を生成します。" # 説明を更新
    bl_options = {'REGISTER', 'UNDO'} # 指示通りに修正

    def execute(self, context):
        log_info("--- プロパティ名診断 ---")
        log_info(f"context.scene.adaptive_wear_generator_pro が存在するか: {'adaptive_wear_generator_pro_props' in context.scene}")
        log_info(f"context.scene.adaptive_wear_generator_pro が存在するか: {'adaptive_wear_generator_pro' in context.scene}")
        log_info("----------------------")
        props = context.scene.adaptive_wear_generator_pro

        base_body = props.base_body
        wear_type = props.wear_type
        tight_fit = props.tight_fit
        thickness = props.thickness

        log_info("--- AWG Generate Wear Operator ---")
        log_info(f"Base Body: {base_body.name if base_body else 'None'}")
        log_info(f"Wear Type: {wear_type}")
        log_info(f"Tight Fit: {tight_fit}")
        log_info(f"Thickness: {thickness}")

        # wear_types.json から追加設定プロパティの情報を読み込む
        # このパスはアドオンのルートからの相対パスである必要があります。
        # アドオンのパスを取得する方法に注意してください。
        # ここでは、bpy.utils.script_path_user() や __file__ を使って
        # アドオンのディレクトリを取得し、そこからの相対パスで presets/wear_types.json を指定します。
        # 簡単のため、ここでは固定パスとしていますが、実際には動的に解決すべきです。
        # (ただし、現在の環境では直接ファイルパスを指定できるため、このままとします)

        # Get addon preferences to access wear_types.json content if stored there
        # For now, assuming direct read or preloaded data
        # For this exercise, we'll simulate loading it. In a real addon, this might be loaded at registration.

        # presets/wear_types.json の内容を文字列として取得 (実際にはファイル読み込み)
        # この部分は、ユーザーが提供したファイル内容を直接利用します。
        # 実際のファイル読み込みは、BlenderのPython環境では以下のように行います。
        # import os
        # addon_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        # wear_types_file_path = os.path.join(addon_dir, "presets", "wear_types.json")
        # try:
        #     with open(wear_types_file_path, 'r') as f:
        #         wear_types_data_str = f.read()
        #     wear_types_data = json.loads(wear_types_data_str)
        # except Exception as e:
        #     log_error(f"Failed to load or parse wear_types.json: {e}")
        #     wear_types_data = []
        #
        # 今回は、事前に読み込んだものを使用する想定で進めます。
        # ユーザーから提供された wear_types.json の内容を直接利用します。
        # この文字列は、実際の tool use で取得したものを想定しています。
        wear_types_json_content = """
[
  {
    "id": "Socks",
    "name": "Socks",
    "description": "Generate socks.",
    "additional_props": ["sock_length"]
  },
  {
    "id": "Gloves",
    "name": "Gloves",
    "description": "Generate gloves.",
    "additional_props": ["glove_fingers"]
  },
  {
    "id": "Pants",
    "name": "Pants",
    "description": "Generate pants.",
    "additional_props": []
  },
  {
    "id": "Tshirt",
    "name": "T-shirt",
    "description": "Generate a T-shirt.",
    "additional_props": []
  }
]
"""
        try:
            wear_types_config = json.loads(wear_types_json_content)
        except json.JSONDecodeError:
            log_info("Error decoding wear_types.json content.")
            wear_types_config = []


        additional_settings = {}
        current_wear_type_info = next((item for item in wear_types_config if item["id"] == wear_type), None)

        if current_wear_type_info and "additional_props" in current_wear_type_info:
            for prop_name in current_wear_type_info["additional_props"]:
                if hasattr(props, prop_name):
                    additional_settings[prop_name] = getattr(props, prop_name)
                    log_info(f"  - Additional Prop: {prop_name} = {additional_settings[prop_name]}")
                else:
                    log_info(f"  - Warning: Property '{prop_name}' not found in addon properties for wear type '{wear_type}'.")

        log_info(f"Additional Settings: {additional_settings}")
        log_info("------------------------------------")

        # 1. 入力検証
        if not base_body:
            self.report({'ERROR'}, "ベースボディが設定されていません。")
            log_info("エラー: ベースボディが未設定です。")
            return {'CANCELLED'}

        log_info(f"入力検証OK: ベースボディ '{base_body.name}' が設定されています。")

        # 2. メッシュ生成の呼び出し
        log_info(f"メッシュ生成を開始します... タイプ: {wear_type}")
        generated_mesh = generate_initial_wear_mesh(wear_type, context, additional_settings=additional_settings) # type: ignore

        if not generated_mesh:
            self.report({'ERROR'}, f"初期メッシュの生成に失敗しました: {wear_type}")
            log_info(f"エラー: 初期メッシュの生成に失敗しました (タイプ: {wear_type})。")
            return {'CANCELLED'}

        log_info(f"初期メッシュ '{generated_mesh.name}' が生成されました。") # type: ignore

        # 3. フィット調整の呼び出し
        log_info(f"フィット調整を開始します... 対象: '{generated_mesh.name}', ベース: '{base_body.name}'") # type: ignore
        fitted_mesh = fit_wear_to_body(generated_mesh, base_body, thickness, tight_fit, context) # type: ignore

        if not fitted_mesh:
            # 生成されたメッシュが不要になった場合は削除 (エラー時)
            bpy.data.objects.remove(generated_mesh, do_unlink=True) # type: ignore
            self.report({'ERROR'}, "メッシュのフィット調整に失敗しました。")
            log_info("エラー: メッシュのフィット調整に失敗しました。")
            return {'CANCELLED'}

        log_info(f"フィット調整後のメッシュ '{fitted_mesh.name}' を取得しました。") # type: ignore

        # 4. シーンへの追加
        #   フィット調整された最終的なメッシュオブジェクトを現在のシーンのコレクションに追加
        #   生成されたオブジェクトが選択され、アクティブになるように設定
        try:
            collection = context.scene.collection # 現在のシーンのコレクション
            collection.objects.link(fitted_mesh) # type: ignore

            # 既存の選択を解除
            bpy.ops.object.select_all(action='DESELECT')

            # 新しいオブジェクトを選択しアクティブにする
            context.view_layer.objects.active = fitted_mesh # type: ignore
            fitted_mesh.select_set(True) # type: ignore

            log_info(f"メッシュ '{fitted_mesh.name}' をシーンに追加し、アクティブにしました。") # type: ignore
        except Exception as e: # pylint: disable=broad-except
            # エラーが発生した場合、作成されたオブジェクトをクリーンアップ
            if generated_mesh and generated_mesh.name in bpy.data.objects: # type: ignore
                bpy.data.objects.remove(generated_mesh, do_unlink=True) # type: ignore
            if fitted_mesh and fitted_mesh.name in bpy.data.objects and fitted_mesh != generated_mesh: # type: ignore
                bpy.data.objects.remove(fitted_mesh, do_unlink=True) # type: ignore
            self.report({'ERROR'}, f"シーンへのメッシュ追加中にエラーが発生しました: {e}")
            log_info(f"エラー: シーンへのメッシュ追加中にエラー: {e}")
            return {'CANCELLED'}

        # 5. 成功メッセージ
        success_message = f"衣装 '{fitted_mesh.name}' の生成とフィット調整が正常に完了しました。" # type: ignore
        self.report({'INFO'}, success_message)
        log_info(success_message)
        log_info("--- AWG Generate Wear Operator Finished ---")
        return {'FINISHED'}

class AWGP_OT_GenerateWear(bpy.types.Operator): # 元のクラス定義はそのまま残す（もし必要であれば）
    bl_idname = "awgp.generate_wear" # こちらは古いIDのまま
    bl_label = "衣装生成"
    bl_description = "素体に基づき選択した衣装を自動生成"
    bl_options = {'REGISTER', 'UNDO'}

    garment_type: StringProperty()
    fit_tightly: bpy.props.BoolProperty()
    thickness: bpy.props.FloatProperty()

    def execute(self, context):
        """
        選択された素体と設定に基づいて衣装メッシュを生成するオペレーター。
        主な処理フロー：
        1. UIからプロパティを取得
        2. 素体のバリデーション（存在確認、メッシュタイプ確認）
        3. 衣装タイプに応じたメッシュ生成処理の呼び出し
        4. 生成されたメッシュへの後処理（フィット調整、UV展開、マテリアル適用）
        """
        props = context.scene.adaptive_wear_props
        body = props.base_body # UIから選択された素体を取得

        # --- 素体のバリデーション ---
        # ユーザーが素体を選択しているか、またそれがメッシュオブジェクトであるかを確認します。
        # これにより、以降の処理で予期せぬエラーが発生するのを防ぎます。
        if not body:
            self.report({'ERROR'}, "素体が選択されていません。パネルから素体オブジェクトを選択してください。")
            return {'CANCELLED'}
        if body.type != 'MESH':
            self.report({'ERROR'}, f"選択されたオブジェクト「{body.name}」はメッシュではありません。メッシュオブジェクトを選択してください。")
            return {'CANCELLED'}

        garment = None # 生成される衣装オブジェクトを格納する変数
        # vg_names = [] # Vertex group names might be needed for other types (将来の拡張用コメント)

        # Log received properties for verification (デバッグ用、リリース時にはコメントアウトまたは削除を検討)
        # print(f"Generating garment type: {self.garment_type}")
        # print(f"Fit tightly: {self.fit_tightly}")
        # print(f"Thickness: {self.thickness}")

        # --- 衣装タイプに応じた処理の分岐 ---
        # garment_type プロパティの値に基づいて、対応するメッシュ生成関数を呼び出します。
        # 各衣装タイプで必要な頂点グループが見つからない場合はエラーを報告します。
        if self.garment_type == 'pants':
            # 'pants' タイプは、旧 UNDERWEAR_OT_Generate オペレーターの機能を移植したものです。
            # AdaptiveWearProps の fit_tightly と thickness を使用します。
            vg_candidates = find_vertex_group_by_keyword(body, ["hip", "腰"])
            if not vg_candidates:
                self.report({'ERROR'}, "パンツ生成に必要な頂点グループ（'hip'または'腰'）が見つかりません。素体の頂点グループを確認してください。")
                return {'CANCELLED'}
            garment = create_underwear_pants_mesh(body, vg_candidates, self.fit_tightly, self.thickness)
        elif self.garment_type == 'bra':
            vg_candidates = find_vertex_group_by_keyword(body, ["chest", "breast", "胸"]) # "胸" を追加
            if not vg_candidates:
                self.report({'ERROR'}, "ブラ生成に必要な頂点グループ（'chest', 'breast', または '胸'）が見つかりません。素体の頂点グループを確認してください。")
                return {'CANCELLED'}
            garment = create_underwear_bra_mesh(body, vg_candidates, self.fit_tightly, self.thickness)
        elif self.garment_type == 'socks':
            vg_candidates = find_vertex_group_by_keyword(body, ["foot", "leg", "足", "脚"]) # "足", "脚" を追加
            if not vg_candidates:
                self.report({'ERROR'}, "靴下生成に必要な頂点グループ（'foot', 'leg', '足', または '脚'）が見つかりません。素体の頂点グループを確認してください。")
                return {'CANCELLED'}
            socks_length = props.socks_length # 靴下の長さをプロパティから取得
            garment = create_socks_mesh(body, vg_candidates, self.fit_tightly, self.thickness, length=socks_length)
        elif self.garment_type == 'gloves':
            vg_candidates = find_vertex_group_by_keyword(body, ["hand", "arm", "手", "腕"]) # "手", "腕" を追加
            if not vg_candidates:
                self.report({'ERROR'}, "手袋生成に必要な頂点グループ（'hand', 'arm', '手', または '腕'）が見つかりません。素体の頂点グループを確認してください。")
                return {'CANCELLED'}
            gloves_fingered = props.gloves_fingered # 手袋の指の有無をプロパティから取得
            garment = create_gloves_mesh(body, vg_candidates, self.fit_tightly, self.thickness, fingered=gloves_fingered)
        elif self.garment_type == 'onesie':
            vg_candidates = find_vertex_group_by_keyword(body, ["torso", "body", "胴体"]) # "胴体" を追加
            if not vg_candidates:
                self.report({'ERROR'}, "ワンピース水着生成に必要な頂点グループ（'torso', 'body', または '胴体'）が見つかりません。素体の頂点グループを確認してください。")
                return {'CANCELLED'}
            garment = create_swimsuit_onesie_mesh(body, vg_candidates, self.fit_tightly, self.thickness)
        elif self.garment_type == 'bikini':
            # ビキニは複数の頂点グループセットを検索する可能性があるため、ロジックを調整
            vg_chest_candidates = find_vertex_group_by_keyword(body, ["chest", "breast", "胸"])
            vg_pelvis_candidates = find_vertex_group_by_keyword(body, ["pelvis", "hips", "腰", "骨盤"]) # "骨盤" を追加
            if not vg_chest_candidates or not vg_pelvis_candidates:
                missing_parts = []
                if not vg_chest_candidates: missing_parts.append("胸部 ('chest', 'breast', '胸')")
                if not vg_pelvis_candidates: missing_parts.append("骨盤部 ('pelvis', 'hips', '腰', '骨盤')")
                self.report({'ERROR'}, f"ビキニ生成に必要な頂点グループが見つかりません: {', '.join(missing_parts)}。素体の頂点グループを確認してください。")
                return {'CANCELLED'}
            # create_swimsuit_bikini_mesh は複数の頂点グループリストを引数に取るように変更されている想定
            # もし単一リストを期待する場合は、vg_candidates = vg_chest_candidates + vg_pelvis_candidates のように結合
            garment = create_swimsuit_bikini_mesh(body, vg_chest_candidates + vg_pelvis_candidates, self.fit_tightly, self.thickness)
        elif self.garment_type == 'tights':
            vg_candidates = find_vertex_group_by_keyword(body, ["leg", "pelvis", "脚", "腰", "骨盤"]) # "脚", "腰", "骨盤" を追加
            if not vg_candidates:
                self.report({'ERROR'}, "タイツ生成に必要な頂点グループ（'leg', 'pelvis', '脚', '腰', または '骨盤'）が見つかりません。素体の頂点グループを確認してください。")
                return {'CANCELLED'}
            # Note: opacity and length parameters need to be added to the operator later (将来の拡張用コメント)
            garment = create_tights_mesh(body, vg_candidates, self.fit_tightly, self.thickness)
        else:
            self.report({'ERROR'}, f"未対応の衣装タイプです: {self.garment_type}")
            return {'CANCELLED'}

        # --- 生成されたメッシュへの後処理 ---
        if garment:
            # Fit Engine: 生成された衣装メッシュを選択された素体にフィットさせます。
            # fit_mesh_to_body(garment, body) # この行は AWGP_OT_GenerateWear のもので、新しい fit_wear_to_body とは別
            # UV Tools: 衣装メッシュのUVを展開します。
            unwrap_uv(garment)

            # Material Manager: マテリアルを適用します。
            if self.garment_type == 'pants':
                # 'pants' タイプの場合、特定のラベンダー色のマテリアルを適用します。
                # これは旧 UNDERWEAR_OT_Generate オペレーターの挙動を維持するためです。
                mat = create_lavender_material()
                if mat:
                    garment.data.materials.clear() # 既存のマテリアルをクリア
                    garment.data.materials.append(mat)
            else:
                # その他の衣装タイプには、基本的なマテリアルを適用します。
                apply_basic_material(garment)

            self.report({'INFO'}, f"衣装「{garment.name}」({self.garment_type}) が正常に生成されました。")
            return {'FINISHED'}
        else:
            # このケースは通常、上記の各衣装タイプ分岐内でエラー処理されるため、到達しないはずです。
            # しかし、念のためフォールバックとして残しておきます。
            self.report({'ERROR'}, f"衣装 ({self.garment_type}) の生成に失敗しました。原因不明のエラーです。")
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