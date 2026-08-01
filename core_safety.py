from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def strict_apply_post_processing(self: Any, garment: Any, props: Any) -> None:
    """Apply every requested post-process step or raise.

    The previous implementation caught every exception and returned normally,
    which allowed the Blender operator to report FINISHED even when materials,
    cloth setup, or rigging had failed. This function deliberately has no broad
    exception handler: the operator's outer execute() block converts any failure
    into CANCELLED and leaves an actionable error in the log/UI.
    """

    from . import core_materials, core_utils

    if garment is None or getattr(garment, "type", None) != "MESH":
        raise RuntimeError("generated garment is not a valid mesh object")

    if props.use_text_material and props.material_prompt:
        result = core_materials.apply_text_material(
            garment, props.wear_type, props.material_prompt
        )
    else:
        result = core_materials.apply_default_material(garment, props.wear_type)
    if result is False:
        raise RuntimeError("material application reported failure")

    if props.wear_type == "SKIRT":
        quality_report = core_utils.evaluate_pleats_geometry(
            garment, props.pleat_count
        )
        if not isinstance(quality_report, dict) or "total_score" not in quality_report:
            raise RuntimeError("pleat quality evaluation returned an invalid report")
        if float(quality_report["total_score"]) < 70:
            logger.warning(
                "skirt geometry score is below the review threshold: %s",
                quality_report["total_score"],
            )

    if props.enable_cloth_sim:
        result = core_utils.setup_cloth_simulation(garment, props.base_body)
        if result is False:
            raise RuntimeError("cloth simulation setup reported failure")

    if props.auto_rigging:
        armature = core_utils.find_armature(props.base_body)
        if armature is None:
            raise RuntimeError(
                "auto rigging was requested but no armature was found on the base body"
            )
        result = core_utils.apply_rigging(garment, props.base_body, armature)
        if result is False:
            raise RuntimeError("rigging transfer reported failure")


def install_strict_generation_contract(core_operators: Any) -> None:
    """Install the fail-closed method before Blender registers the operator."""

    operator = core_operators.AWGP_OT_GenerateWear
    operator._apply_post_processing = strict_apply_post_processing
    operator.bl_description = (
        "ルールベースで衣装候補を生成します。全ての要求工程が成功した場合のみ完了します"
    )
