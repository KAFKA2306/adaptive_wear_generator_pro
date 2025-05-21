import bpy
from bpy.props import EnumProperty

class AdaptiveWearProps(bpy.types.PropertyGroup):
    garment_type: EnumProperty(
        name="衣装タイプ",
        items=[
            ('pants', 'パンツ', ''),
            ('bra', 'ブラ', ''),
            ('socks', '靴下', ''),
            ('gloves', '手袋', ''),
            ('tshirt', 'Tシャツ', ''),
            ('hoodie', 'パーカー', ''),
            ('skirt', 'スカート', ''),
            ('dress', 'ワンピース', '')
        ],
        default='pants'
    )

    fit_tightly: bpy.props.BoolProperty(
        name="フィット感を密着させる",
        description="生成される衣装を素体に密着させるかどうか",
        default=True
    )

    thickness: bpy.props.FloatProperty(
        name="厚み",
        description="生成される衣装の厚み",
        default=1.0,
        min=0.01,
        max=10.0
    )

class UnderwearProps(bpy.types.PropertyGroup):
    base_body: bpy.props.PointerProperty(
        name="素体",
        type=bpy.types.Object,
        description="下着を生成する素体"
    )