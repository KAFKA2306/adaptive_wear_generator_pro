import bpy
from bpy.props import EnumProperty

class AdaptiveWearProps(bpy.types.PropertyGroup):
    garment_type: EnumProperty(
        name="衣装タイプ",
        items=[
            ('pants', 'パンツ', ''),
            ('bra', 'ブラ', ''),
            ('socks', '靴下', ''),
            ('gloves', '手袋', '')
        ],
        default='pants'
    )