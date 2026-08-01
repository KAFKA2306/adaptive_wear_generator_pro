bl_info = {
    "name": "AdaptiveWear Generator Pro",
    "author": "AdaptiveWear Team",
    "version": (4, 1, 1),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > AdaptiveWear",
    "description": "ルールベースの密着衣装候補生成・診断アドオン",
    "category": "Object",
}

import logging
import sys
from typing import List

import bpy
from bpy.props import PointerProperty

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    if any(getattr(handler, "_adaptive_wear", False) for handler in logger.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler._adaptive_wear = True
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def register() -> None:
    logger.info("=== AdaptiveWear Generator Pro v4.1.1 登録開始 ===")
    setup_logging()
    try:
        from . import core_operators, core_properties, core_safety, ui_panels

        # Replace the legacy post-processing method before Blender registers the
        # operator. Failures now propagate to execute(), which returns CANCELLED.
        core_safety.install_strict_generation_contract(core_operators)

        if hasattr(bpy.types.Scene, "adaptive_wear_generator_pro"):
            del bpy.types.Scene.adaptive_wear_generator_pro

        registration_classes = [
            core_properties.AWGProPropertyGroup,
            core_operators.AWGP_OT_GenerateWear,
            core_operators.AWGP_OT_DiagnoseBones,
            ui_panels.AWG_PT_MainPanel,
            ui_panels.AWG_PT_AdvancedPanel,
            ui_panels.AWG_PT_HelpPanel,
        ]
        registered = []
        for cls in registration_classes:
            try:
                bpy.utils.register_class(cls)
                registered.append(cls)
            except Exception:
                _rollback_registration(registered)
                raise

        bpy.types.Scene.adaptive_wear_generator_pro = PointerProperty(
            type=core_properties.AWGProPropertyGroup
        )
        logger.info("=== AdaptiveWear Generator Pro 登録完了 ===")
    except Exception:
        logger.exception("AdaptiveWear Generator Pro registration failed")
        raise


def unregister() -> None:
    logger.info("=== AdaptiveWear Generator Pro 登録解除開始 ===")
    if hasattr(bpy.types.Scene, "adaptive_wear_generator_pro"):
        del bpy.types.Scene.adaptive_wear_generator_pro

    try:
        from . import core_operators, core_properties, ui_panels
    except ImportError:
        logger.warning("modules are unavailable; unregister ended")
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
        except Exception:
            logger.exception("failed to unregister %s", cls.__name__)
    logger.info("=== AdaptiveWear Generator Pro 登録解除完了 ===")


def _rollback_registration(registered_classes: List) -> None:
    for cls in reversed(registered_classes):
        try:
            if hasattr(cls, "bl_rna"):
                bpy.utils.unregister_class(cls)
        except Exception:
            logger.exception("rollback failed for %s", cls.__name__)


if __name__ == "__main__":
    register()
