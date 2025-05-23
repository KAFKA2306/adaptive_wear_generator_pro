# core/diagnostic_operators.py

import bpy
from bpy.types import Operator
from . import bone_utils
from ..services import logging_service


class AWGP_OT_DiagnoseBones(Operator):
    """ボーンと頂点グループの診断オペレーター"""

    bl_idname = "awgp.diagnose_bones"
    bl_label = "Diagnose Bones & Vertex Groups"
    bl_description = "ボーンと頂点グループの対応関係を診断します"
    bl_options = {"REGISTER"}

    def execute(self, context):
        scene = context.scene
        props = scene.adaptive_wear_generator_pro

        if not props.base_body:
            self.report({"ERROR"}, "素体メッシュを選択してください")
            return {"CANCELLED"}

        # アーマチュアを検索
        armature = None
        for modifier in props.base_body.modifiers:
            if modifier.type == "ARMATURE" and modifier.object:
                armature = modifier.object
                break

        if not armature:
            self.report(
                {"WARNING"},
                "アーマチュアが見つかりませんが、頂点グループのみ診断します",
            )

        # 診断実行
        bone_utils.diagnose_bone_vertex_group_mapping(props.base_body, armature)

        # 手関連の特別診断
        left_hand, right_hand = bone_utils.find_hand_vertex_groups(props.base_body)

        result_msg = "診断完了。詳細はシステムコンソールを確認してください。"
        if left_hand and right_hand:
            result_msg += f" 手の頂点グループ: {left_hand.name}, {right_hand.name}"
        elif left_hand or right_hand:
            found = left_hand or right_hand
            result_msg += f" 片手の頂点グループのみ発見: {found.name}"
        else:
            result_msg += " 手の頂点グループが見つかりませんでした。"

        self.report({"INFO"}, result_msg)
        return {"FINISHED"}


# 登録用のクラスリスト
classes = (AWGP_OT_DiagnoseBones,)

logging_service.log_info("'core.diagnostic_operators' モジュールがロードされました。")
