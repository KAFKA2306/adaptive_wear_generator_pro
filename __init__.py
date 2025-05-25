bl_info = {
    "name": "AdaptiveWear Generator Pro",
    "author": "AdaptiveWear Team",
    "version": (4, 0, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > AdaptiveWear",
    "description": "AI駆動の高品質密着衣装自動生成アドオン（完全統合版）",
    "category": "Object",
}

import bpy
from bpy.props import PointerProperty


def register():
    """アドオン登録処理"""
    print("=== AdaptiveWear Generator Pro v4.0.0 登録開始 ===")

    try:
        # モジュールインポート
        from . import core
        from . import ui

        print("モジュールインポート成功")

        # 既存プロパティの安全な削除
        if hasattr(bpy.types.Scene, "adaptive_wear_generator_pro"):
            del bpy.types.Scene.adaptive_wear_generator_pro
            print("既存プロパティを削除しました")

        # クラス登録リスト
        registration_classes = [
            core.AWGProPropertyGroup,
            core.AWGP_OT_GenerateWear,
            core.AWGP_OT_DiagnoseBones,
            ui.AWG_PT_MainPanel,
        ]

        # 各クラスを順次登録
        for cls in registration_classes:
            try:
                bpy.utils.register_class(cls)
                print(f"[SUCCESS] {cls.__name__} 登録完了")
            except Exception as e:
                print(f"[ERROR] {cls.__name__} 登録失敗: {e}")
                # 既に登録されたクラスをロールバック
                _rollback_registration(
                    registration_classes[: registration_classes.index(cls)]
                )
                return

        # シーンプロパティの設定
        bpy.types.Scene.adaptive_wear_generator_pro = PointerProperty(
            type=core.AWGProPropertyGroup
        )
        print("シーンプロパティ設定完了")

        print("=== AdaptiveWear Generator Pro 登録完了 ===")

    except ImportError as e:
        print(f"=== モジュールインポートエラー: {str(e)} ===")
    except Exception as e:
        print(f"=== 登録エラー: {str(e)} ===")
        import traceback

        traceback.print_exc()


def unregister():
    """アドオン登録解除処理"""
    print("=== AdaptiveWear Generator Pro 登録解除開始 ===")

    try:
        # シーンプロパティの削除
        if hasattr(bpy.types.Scene, "adaptive_wear_generator_pro"):
            del bpy.types.Scene.adaptive_wear_generator_pro
            print("シーンプロパティを削除しました")

        # モジュール存在確認
        try:
            from . import core
            from . import ui
        except ImportError:
            print("モジュールが見つかりません - 終了")
            return

        # クラス登録解除リスト（逆順）
        unregistration_classes = [
            ui.AWG_PT_MainPanel,
            core.AWGP_OT_DiagnoseBones,
            core.AWGP_OT_GenerateWear,
            core.AWGProPropertyGroup,
        ]

        # 各クラスを順次登録解除
        for cls in unregistration_classes:
            try:
                if hasattr(cls, "bl_rna"):
                    bpy.utils.unregister_class(cls)
                    print(f"[SUCCESS] {cls.__name__} 登録解除完了")
                else:
                    print(f"[SKIP] {cls.__name__} は既に登録解除済み")
            except Exception as e:
                print(f"[ERROR] {cls.__name__} 登録解除失敗: {e}")

        print("=== AdaptiveWear Generator Pro 登録解除完了 ===")

    except Exception as e:
        print(f"=== 登録解除エラー: {str(e)} ===")


def _rollback_registration(registered_classes):
    """登録に失敗した場合のロールバック処理"""
    print("登録ロールバック開始...")
    for cls in reversed(registered_classes):
        try:
            if hasattr(cls, "bl_rna"):
                bpy.utils.unregister_class(cls)
                print(f"[ROLLBACK] {cls.__name__} 登録解除")
        except Exception as e:
            print(f"[ROLLBACK ERROR] {cls.__name__}: {e}")


if __name__ == "__main__":
    register()
