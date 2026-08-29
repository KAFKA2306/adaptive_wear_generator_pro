"""生成された衣装メッシュの最低限の整合性をBlender上で確認する。"""

import json
import logging
import math
import os
import sys
import traceback
from pathlib import Path
from typing import Any

import bpy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

addon_root = Path(os.environ["BLENDER_ADDON_PATH"]) / "adaptive_wear_generator_pro"
if str(addon_root) not in sys.path:
    sys.path.append(str(addon_root))


def setup_test_environment() -> bpy.types.Object:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.preferences.addon_enable(module="adaptive_wear_generator_pro")

    bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 1), radius=1.0)
    body = bpy.context.active_object
    body.name = "TestBody"

    names = ("hip", "chest", "arm_l", "arm_r", "leg_l", "leg_r", "foot_l", "foot_r", "hand_l", "hand_r")
    groups = {name: body.vertex_groups.new(name=name) for name in names}
    for vertex in body.data.vertices:
        x, z, index = vertex.co.x, vertex.co.z, vertex.index
        if z >= 0.20:
            groups["chest"].add([index], 1.0, "REPLACE")
        if -0.20 <= z < 0.25:
            groups["hip"].add([index], 1.0, "REPLACE")
        if -0.80 <= z < -0.15:
            groups["leg_r" if x >= 0 else "leg_l"].add([index], 1.0, "REPLACE")
        if z < -0.65:
            groups["foot_r" if x >= 0 else "foot_l"].add([index], 1.0, "REPLACE")
        if z >= 0.0 and abs(x) >= 0.25:
            groups["arm_r" if x >= 0 else "arm_l"].add([index], 1.0, "REPLACE")
        if z >= -0.15 and abs(x) >= 0.70:
            groups["hand_r" if x >= 0 else "hand_l"].add([index], 1.0, "REPLACE")
    return body


def generate_garment(body: bpy.types.Object, wear_type: str) -> bpy.types.Object:
    props = bpy.context.scene.adaptive_wear_generator_pro
    props.base_body = body
    props.wear_type = wear_type
    props.quality_level = "MEDIUM"
    props.auto_rigging = False
    if wear_type == "SKIRT":
        props.pleat_count = 12
        props.skirt_length = 0.5

    before = {obj.name for obj in bpy.data.objects}
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    result = bpy.ops.awgp.generate_wear()
    if "FINISHED" not in result:
        raise RuntimeError(f"生成オペレーターが失敗しました: {result}")

    created = [obj for obj in bpy.data.objects if obj.name not in before and obj != body and obj.type == "MESH"]
    active = bpy.context.view_layer.objects.active
    if active in created:
        return active
    if len(created) == 1:
        return created[0]
    raise RuntimeError(f"生成メッシュを一意に特定できません: {[obj.name for obj in created]}")


def run_integrity_checks(obj: bpy.types.Object) -> dict[str, Any]:
    mesh = obj.data
    checks: dict[str, Any] = {
        "is_mesh": obj.type == "MESH",
        "vertex_count": len(mesh.vertices),
        "edge_count": len(mesh.edges),
        "polygon_count": len(mesh.polygons),
        "finite_coordinates": all(
            math.isfinite(value)
            for vertex in mesh.vertices
            for value in (vertex.co.x, vertex.co.y, vertex.co.z)
        ),
        "valid_polygons": all(polygon.loop_total >= 3 for polygon in mesh.polygons),
    }
    issues = []
    if not checks["is_mesh"]:
        issues.append("生成物がメッシュではありません")
    if checks["vertex_count"] == 0:
        issues.append("頂点がありません")
    if checks["edge_count"] == 0:
        issues.append("辺がありません")
    if checks["polygon_count"] == 0:
        issues.append("面がありません")
    if not checks["finite_coordinates"]:
        issues.append("有限値ではない頂点座標があります")
    if not checks["valid_polygons"]:
        issues.append("3頂点未満の面があります")

    return {"checks": checks, "issues": issues, "overall_pass": not issues}


def save(results: dict[str, Any], output_dir: str, wear_type: str) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stem = wear_type.lower()
    (output / f"mesh_integrity_results_{stem}.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        f"# AdaptiveWear Generator Pro メッシュ整合性テスト ({wear_type})",
        "",
        f"Blenderバージョン: {bpy.app.version_string}",
        "",
    ]
    for key, value in results.get("checks", {}).items():
        lines.append(f"- {key}: {value}")
    for issue in results.get("issues", []):
        lines.append(f"- 課題: {issue}")
    lines.append("")
    lines.append(f"総合結果: {'PASS' if results.get('overall_pass') else 'FAIL'}")
    (output / f"mesh_integrity_report_{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    output_dir = "test-results/mesh-integrity"
    wear_type = "T_SHIRT"
    for index, arg in enumerate(argv):
        if arg == "--output-dir" and index + 1 < len(argv):
            output_dir = argv[index + 1]
        elif arg == "--wear-type" and index + 1 < len(argv):
            wear_type = argv[index + 1].upper()

    try:
        body = setup_test_environment()
        garment = generate_garment(body, wear_type)
        results = run_integrity_checks(garment)
    except Exception as exc:
        traceback.print_exc()
        results = {"checks": {}, "issues": [str(exc)], "overall_pass": False}

    save(results, output_dir, wear_type)
    raise SystemExit(0 if results["overall_pass"] else 1)


if __name__ == "__main__":
    main()
