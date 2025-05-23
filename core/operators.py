# core/operators.py

import bpy
from bpy.types import Operator
from . import mesh_generator
from . import fit_engine
from . import bone_brendshape_weight_transfer
from . import material_generator
from ..services import logging_service


class AWGP_OT_GenerateWear(Operator):
    """AdaptiveWear Generator Pro: 高精度衣装生成オペレーター"""

    bl_idname = "awgp.generate_wear"
    bl_label = "Generate Wear"
    bl_description = "選択された設定に基づいて高品質な衣装を生成します"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        props = scene.adaptive_wear_generator_pro

        if not self.validate_inputs(props):
            return {"CANCELLED"}

        base_obj = props.base_body
        wear_type = props.wear_type

        logging_service.log_info(
            f"高精度衣装生成開始: {wear_type} (素体: {base_obj.name})"
        )

        created_objects = []
        try:
            # 1. メッシュ生成
            generated_garment = mesh_generator.generate_wear_mesh(
                base_obj, wear_type, props
            )

            if generated_garment is None:
                self.report({"ERROR"}, "メッシュ生成に失敗しました")
                return {"CANCELLED"}

            created_objects.append(generated_garment)

            # 2. フィッティング処理（将来実装）
            try:
                if hasattr(fit_engine, "apply_fitting"):
                    if not fit_engine.apply_fitting(generated_garment, base_obj, props):
                        self.report(
                            {"WARNING"},
                            "フィッティング処理に失敗しましたが、処理を続行します",
                        )
            except ImportError:
                logging_service.log_info(
                    "フィッティングエンジンが見つかりません。スキップします。"
                )

            # 3. リギング処理（将来実装）
            base_armature = self.get_base_armature(base_obj)
            if base_armature:
                try:
                    if hasattr(bone_brendshape_weight_transfer, "apply_rigging"):
                        if not bone_brendshape_weight_transfer.apply_rigging(
                            generated_garment, base_obj, base_armature
                        ):
                            self.report(
                                {"WARNING"},
                                "リギング処理に失敗しましたが、処理を続行します",
                            )
                except ImportError:
                    logging_service.log_info(
                        "リギングモジュールが見つかりません。スキップします。"
                    )
            else:
                logging_service.log_info(
                    "アーマチュアが見つかりません。リギングをスキップします。"
                )

            # 4. マテリアル適用（将来実装）
            try:
                if hasattr(material_generator, "apply_wear_material"):
                    if not material_generator.apply_wear_material(
                        generated_garment, wear_type, props
                    ):
                        self.report(
                            {"WARNING"},
                            "マテリアル適用に失敗しましたが、処理を続行します",
                        )
                else:
                    # 基本的なマテリアル作成
                    self.create_basic_material(generated_garment, wear_type)
            except ImportError:
                logging_service.log_info(
                    "マテリアルジェネレーターが見つかりません。基本マテリアルを作成します。"
                )
                self.create_basic_material(generated_garment, wear_type)

            # 5. オブジェクトを選択状態にする
            bpy.ops.object.select_all(action="DESELECT")
            generated_garment.select_set(True)
            context.view_layer.objects.active = generated_garment

            self.report({"INFO"}, f"{wear_type} の生成が完了しました")
            logging_service.log_info("衣装生成処理が正常に完了しました")
            return {"FINISHED"}

        except Exception as e:
            error_msg = f"衣装生成中にエラーが発生しました: {str(e)}"
            self.report({"ERROR"}, error_msg)
            logging_service.log_error(error_msg)
            self.cleanup_objects(created_objects)
            return {"CANCELLED"}

    def validate_inputs(self, props):
        """入力値の検証"""
        if props.base_body is None:
            self.report({"ERROR"}, "素体メッシュを選択してください")
            return False

        if props.base_body.type != "MESH":
            self.report({"ERROR"}, "選択されたオブジェクトがメッシュではありません")
            return False

        if props.wear_type == "NONE":
            self.report({"ERROR"}, "生成する衣装タイプを選択してください")
            return False

        if len(props.base_body.data.vertices) == 0:
            self.report({"ERROR"}, "素体メッシュに頂点がありません")
            return False

        return True

    def get_base_armature(self, base_obj):
        """素体に関連付けられたアーマチュアを取得"""
        for modifier in base_obj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object:
                return modifier.object
        return None

    def create_basic_material(self, obj, wear_type):
        """基本的なマテリアルを作成（minimal_value_productを参考）"""
        try:
            # 衣装タイプに応じた色設定
            color_map = {
                "PANTS": (0.7, 0.5, 1.0, 1.0),  # ラベンダー
                "BRA": (1.0, 0.7, 0.8, 1.0),  # ピンク
                "T_SHIRT": (0.8, 0.8, 1.0, 1.0),  # ライトブルー
                "SOCKS": (0.9, 0.9, 0.9, 1.0),  # ホワイト
                "GLOVES": (0.6, 0.4, 0.2, 1.0),  # ブラウン
            }

            base_color = color_map.get(wear_type, (0.8, 0.8, 0.8, 1.0))

            # マテリアル作成
            mat_name = f"{obj.name}_material"
            mat = bpy.data.materials.new(mat_name)
            mat.use_nodes = True
            mat.blend_method = "BLEND"

            # ノード設定
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # 既存ノードを削除
            for node in nodes:
                nodes.remove(node)

            # 新しいノードを作成
            output_node = nodes.new("ShaderNodeOutputMaterial")
            bsdf_node = nodes.new("ShaderNodeBsdfPrincipled")

            # ノード位置設定
            output_node.location = (200, 0)
            bsdf_node.location = (0, 0)

            # マテリアルプロパティ設定
            bsdf_node.inputs["Base Color"].default_value = base_color
            bsdf_node.inputs["Alpha"].default_value = 0.8  # 半透明

            # Blender 4.x対応: Specular設定
            if "Specular" in bsdf_node.inputs:
                bsdf_node.inputs["Specular"].default_value = 0.5
            elif "Specular IOR Level" in bsdf_node.inputs:
                bsdf_node.inputs["Specular IOR Level"].default_value = 0.5

            # ノードを接続
            links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])

            # オブジェクトにマテリアルを適用
            obj.data.materials.clear()
            obj.data.materials.append(mat)

            logging_service.log_info(
                f"基本マテリアル '{mat_name}' を作成・適用しました"
            )

        except Exception as e:
            logging_service.log_warning(f"基本マテリアル作成エラー: {str(e)}")

    def cleanup_objects(self, objects):
        """エラー時のオブジェクトクリーンアップ"""
        for obj in objects:
            if obj and obj.name in bpy.data.objects:
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                    logging_service.log_info(
                        f"クリーンアップ: {obj.name} を削除しました"
                    )
                except Exception as e:
                    logging_service.log_warning(f"オブジェクト削除警告: {str(e)}")


# ★重要★ このモジュールで登録するクラスをタプルにまとめる
classes = (AWGP_OT_GenerateWear,)

logging_service.log_info("'core.operators' モジュールがロードされました。")
