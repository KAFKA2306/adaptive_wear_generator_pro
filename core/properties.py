import bpy
from bpy.props import (
    PointerProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
)
from bpy.types import PropertyGroup, Object


def get_wear_types_items(self, context):
    return [
        ("NONE", "未選択", "衣装タイプが選択されていません"),
        ("T_SHIRT", "Tシャツ", "Tシャツを生成"),
        ("PANTS", "パンツ", "パンツを生成"),
        ("SOCKS", "靴下", "靴下を生成"),
        ("GLOVES", "手袋", "手袋を生成"),
    ]


class AdaptiveWearGeneratorProPropertyGroup(PropertyGroup):
    base_body: PointerProperty(
        name="素体メッシュ",
        description="衣装を適用するベースとなるメッシュオブジェクト",
        type=Object,
        poll=lambda self, obj: obj.type == "MESH",
    )
    wear_type: EnumProperty(
        name="衣装タイプ",
        description="生成する衣装のタイプを選択します",
        items=get_wear_types_items,
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
    )
    sock_length: FloatProperty(
        name="靴下の長さ",
        description="靴下の長さを設定します (例: 0.0で足首、1.0で膝上など)",
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

    thickness: FloatProperty(
        name="厚み",
        description="衣装の厚みを設定します",
        default=0.01,
        min=0.0,
        soft_min=0.0,
        soft_max=0.1,
        step=0.1,
        precision=3,
    )
