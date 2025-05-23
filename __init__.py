# __init__.py

bl_info = {
    "name": "AdaptiveWear Generator Pro",
    "author": "AdaptiveWear Team",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > AdaptiveWear",
    "description": "AI駆動の密着衣装自動生成アドオン",
    "category": "Object",
}

import bpy
import importlib
import logging
from bpy.props import PointerProperty
from bpy.types import Scene

# モジュールインポート
MODULE_NAMES = (
    "services.logging_service",
    "core.properties",
    "core.bone_utils",
    "core.mesh_generator",
    "core.operators",
    "core.diagnostic_operators",
    "ui.panel_main",
)

# 登録されたクラスを保持するためのグローバル変数
_registered_classes = []


def register_modules():
    """モジュールの動的インポートと登録"""
    global _registered_classes
    _registered_classes.clear()

    for module_name_rel in MODULE_NAMES:
        try:
            module = importlib.import_module(f".{module_name_rel}", package=__package__)
            importlib.reload(module)

            if hasattr(module, "classes") and isinstance(module.classes, tuple):
                for cls in module.classes:
                    try:
                        bpy.utils.register_class(cls)
                        _registered_classes.append(cls)
                        print(f"AdaptiveWear: クラス '{cls.__name__}' を登録しました")
                    except Exception as e:
                        print(
                            f"AdaptiveWear: クラス '{cls.__name__}' の登録に失敗 - {str(e)}"
                        )
            else:
                print(
                    f"AdaptiveWear: モジュール '{module_name_rel}' に 'classes' タプルが見つかりません"
                )

            print(f"AdaptiveWear: モジュール '{module_name_rel}' の登録処理完了")

        except ImportError as e:
            print(
                f"AdaptiveWear: モジュール '{module_name_rel}' のインポートに失敗 - {str(e)}"
            )
        except Exception as e:
            print(
                f"AdaptiveWear: モジュール '{module_name_rel}' の登録中に予期せぬエラー - {str(e)}"
            )


def unregister_modules():
    """モジュールの登録解除"""
    global _registered_classes
    for cls in reversed(_registered_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            print(
                f"AdaptiveWear: クラス '{cls.__name__}' の登録解除中にランタイムエラー（無視）"
            )
        except Exception as e:
            print(
                f"AdaptiveWear: クラス '{cls.__name__}' の登録解除中に予期せぬエラー - {str(e)}"
            )
    _registered_classes.clear()
    print("AdaptiveWear: 全モジュールのクラス登録解除完了")


def register():
    """アドオン有効化時の処理"""
    print("=" * 40)
    print(f"AdaptiveWear Generator Pro v{bl_info['version']} 登録開始...")

    # 1. 各モジュールのクラスを登録
    register_modules()

    # 2. シーンプロパティの登録
    try:
        from .core.properties import AdaptiveWearGeneratorProPropertyGroup

        Scene.adaptive_wear_generator_pro = PointerProperty(
            type=AdaptiveWearGeneratorProPropertyGroup
        )
        print("AdaptiveWear: シーンプロパティ 'adaptive_wear_generator_pro' 登録成功")
    except ImportError:
        print(
            "AdaptiveWear: エラー - 'AdaptiveWearGeneratorProPropertyGroup' が 'core.properties' からインポートできませんでした"
        )
    except Exception as e:
        print(f"AdaptiveWear: シーンプロパティ登録エラー - {str(e)}")

    # 3. ロギングサービスの初期化
    try:
        from .services import logging_service

        logging_service.initialize_logging(
            log_level=logging.DEBUG,
            log_to_file=True,
            log_filename=f"{bl_info['name'].replace(' ', '_')}.log",
        )
        print("AdaptiveWear: ロギングサービス初期化完了")
    except ImportError:
        print("AdaptiveWear: エラー - 'logging_service' が見つかりませんでした")
    except Exception as e:
        print(f"AdaptiveWear: ロギングサービス初期化エラー - {str(e)}")

    print(
        f"AdaptiveWear Generator Pro 登録完了 (登録クラス数: {len(_registered_classes)})"
    )
    print("=" * 40)


def unregister():
    """アドオン無効化時の処理"""
    print("=" * 40)
    print("AdaptiveWear Generator Pro 登録解除開始...")

    # 1. シーンプロパティの削除
    if hasattr(Scene, "adaptive_wear_generator_pro"):
        try:
            del Scene.adaptive_wear_generator_pro
            print(
                "AdaptiveWear: シーンプロパティ 'adaptive_wear_generator_pro' 削除完了"
            )
        except Exception as e:
            print(f"AdaptiveWear: シーンプロパティ削除エラー - {str(e)}")
    else:
        print(
            "AdaptiveWear: シーンプロパティ 'adaptive_wear_generator_pro' は存在しませんでした"
        )

    # 2. 各モジュールのクラスを登録解除
    unregister_modules()

    # 3. ロギングサービスのシャットダウン
    try:
        from .services import logging_service

        logging_service.shutdown_logging()
        print("AdaptiveWear: ロギングサービスシャットダウン完了")
    except Exception as e:
        print(f"AdaptiveWear: ロギングサービスシャットダウンエラー - {str(e)}")

    print("AdaptiveWear Generator Pro 登録解除完了")
    print("=" * 40)


if __name__ == "__main__":
    register()
