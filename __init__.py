bl_info = {
    "name": "AdaptiveWear Generator Pro",
    "author": "AdaptiveWear Team",
    "version": (4, 1, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > AdaptiveWear",
    "description": "AI駆動の高品質密着衣装自動生成アドオン（リファクタリング版）",
    "category": "Object",
}

import bpy
from bpy.props import PointerProperty
from typing import Set, List
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def register() -> None:
    logger.info("=== AdaptiveWear Generator Pro v4.1.0 登録開始 ===")
    try:
        setup_logging()
        from . import (
            core_properties,
            core_operators,
            core_generators,
            core_utils,
            ui_panels,
        )

        logger.info("モジュールインポート成功")

        if hasattr(bpy.types.Scene, "adaptive_wear_generator_pro"):
            del bpy.types.Scene.adaptive_wear_generator_pro
            logger.info("既存プロパティを削除しました")

        registration_classes = [
            core_properties.AWGProPropertyGroup,
            core_operators.AWGP_OT_GenerateWear,
            core_operators.AWGP_OT_DiagnoseBones,
            ui_panels.AWG_PT_MainPanel,
            ui_panels.AWG_PT_AdvancedPanel,
            ui_panels.AWG_PT_HelpPanel,
        ]

        for cls in registration_classes:
            try:
                bpy.utils.register_class(cls)
                logger.info(f"[SUCCESS] {cls.__name__} 登録完了")
            except Exception as e:
                logger.error(f"[ERROR] {cls.__name__} 登録失敗: {e}")
                _rollback_registration(
                    registration_classes[: registration_classes.index(cls)]
                )
                return

        bpy.types.Scene.adaptive_wear_generator_pro = PointerProperty(
            type=core_properties.AWGProPropertyGroup
        )
        logger.info("=== AdaptiveWear Generator Pro 登録完了 ===")
    except ImportError as e:
        logger.error(f"=== モジュールインポートエラー: {str(e)} ===")
    except Exception as e:
        logger.error(f"=== 登録エラー: {str(e)} ===")
        import traceback

        traceback.print_exc()


def unregister() -> None:
    logger.info("=== AdaptiveWear Generator Pro 登録解除開始 ===")
    try:
        if hasattr(bpy.types.Scene, "adaptive_wear_generator_pro"):
            del bpy.types.Scene.adaptive_wear_generator_pro
            logger.info("シーンプロパティを削除しました")

        try:
            from . import core_properties, core_operators, ui_panels
        except ImportError:
            logger.warning("モジュールが見つかりません - 終了")
            return

        unregistration_classes = [
            ui_panels.AWG_PT_HelpPanel,
            ui_panels.AWG_PT_AdvancedPanel,
            ui_panels.AWG_PT_MainPanel,
            core_operators.AWGP_OT_DiagnoseBones,
            core_operators.AWGP_OT_GenerateWear,
            core_properties.AWGProPropertyGroup,
        ]

        for cls in unregistration_classes:
            try:
                if hasattr(cls, "bl_rna"):
                    bpy.utils.unregister_class(cls)
                    logger.info(f"[SUCCESS] {cls.__name__} 登録解除完了")
                else:
                    logger.info(f"[SKIP] {cls.__name__} は既に登録解除済み")
            except Exception as e:
                logger.error(f"[ERROR] {cls.__name__} 登録解除失敗: {e}")
        logger.info("=== AdaptiveWear Generator Pro 登録解除完了 ===")
    except Exception as e:
        logger.error(f"=== 登録解除エラー: {str(e)} ===")


def _rollback_registration(registered_classes: List) -> None:
    logger.warning("登録ロールバック開始...")
    for cls in reversed(registered_classes):
        try:
            if hasattr(cls, "bl_rna"):
                bpy.utils.unregister_class(cls)
                logger.info(f"[ROLLBACK] {cls.__name__} 登録解除")
        except Exception as e:
            logger.error(f"[ROLLBACK ERROR] {cls.__name__}: {e}")


if __name__ == "__main__":
    register()
