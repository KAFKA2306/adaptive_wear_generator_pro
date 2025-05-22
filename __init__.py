bl_info = {
    "name": "AdaptiveWear Generator Pro",
    "author": "Your Name",
    "version": (0, 1, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > AdaptiveWear",
    "description": "密着衣装を自動生成するアドオン",
    "category": "Object",
}

import bpy
from bpy.props import PointerProperty
from . import ui
from . import core
from .core.properties import AdaptiveWearProps, UnderwearProps

# クラスリストで一括管理
classes = (
    AdaptiveWearProps,
    UnderwearProps,  # MVP用プロパティ
    ui.panel_main.UNDERWEAR_PT_Main,  # MVP用パネル
    core.operators.UNDERWEAR_OT_Generate,  # MVP用オペレーター
    # 他にも登録したいクラスがあればここに追加
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.adaptive_wear_props = PointerProperty(type=AdaptiveWearProps)
    bpy.types.Scene.underwear_props = PointerProperty(
        type=UnderwearProps
    )  # MVP用プロパティをシーンにリンク
    ui.register()


def unregister():
    ui.unregister()
    del bpy.types.Scene.adaptive_wear_props
    del bpy.types.Scene.underwear_props  # MVP用プロパティのリンクを解除
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


# ここで register() を直接呼ばない
