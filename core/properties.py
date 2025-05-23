# core/properties.py
import bpy
from bpy.props import (
    PointerProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
)
from bpy.types import PropertyGroup, Object
from ..services import logging_service

# ロガーを取得
logger = logging_service.get_addon_logger()

# EnumProperty のアイテム定義（直接リストとして定義）
WEAR_TYPES_ITEMS = [
    ("NONE", "未選択", "衣装タイプが選択されていません"),
    ("T_SHIRT", "Tシャツ", "Tシャツを生成"),
    ("PANTS", "パンツ", "パンツを生成"),
    ("SOCKS", "靴下", "靴下を生成"),
    ("GLOVES", "手袋", "手袋を生成"),
    ("BRA", "ブラ", "ブラジャーを生成"),
]


def poll_mesh_objects(self, obj):
    """メッシュオブジェクトのみを選択可能にする"""
    return obj is not None and obj.type == "MESH"


class AdaptiveWearGeneratorProPropertyGroup(PropertyGroup):
    """AdaptiveWear Generator Pro のプロパティグループ"""

    base_body: PointerProperty(
        name="素体メッシュ",
        description="衣装を適用するベースとなるメッシュオブジェクト",
        type=Object,
        poll=poll_mesh_objects,
    )

    wear_type: EnumProperty(
        name="衣装タイプ",
        description="生成する衣装のタイプを選択します",
        items=WEAR_TYPES_ITEMS,  # 関数ではなく直接リストを指定
        default="NONE",  # 文字列で識別子を指定
    )

    tight_fit: BoolProperty(
        name="フィット感を密着させる",
        description="衣装のフィット感を素体に密着させるかどうか",
        default=False,
    )

    thickness: FloatProperty(
        name="厚み",
        description="衣装の厚みを設定します",
        default=0.01,
        min=0.0,
        soft_min=0.0,
        soft_max=0.1,
        step=0.1,
        precision=3,
        unit="LENGTH",
    )

    sock_length: FloatProperty(
        name="靴下の長さ",
        description="靴下の長さを設定します (0.0で足首、1.0で膝上)",
        default=0.5,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    glove_fingers: BoolProperty(
        name="手袋の指の有無",
        description="手袋に指の部分を生成するかどうか",
        default=True,
    )


# このモジュールで登録するクラスをタプルにまとめる
classes = (AdaptiveWearGeneratorProPropertyGroup,)

logging_service.log_info("'core.properties' モジュールがロードされました。")
