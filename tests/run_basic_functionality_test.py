"""Blender上で主要な衣装生成経路が実行できることを確認する。"""

import json
import logging
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
    """実品質ではなく生成経路を検証するための最小メッシュを作る。"""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.preferences.addon_enable(module="adaptive_wear_generator_pro")

    # MeshVertex.co はオブジェクトのローカル座標なので、判定も -1..1 のローカル座標で行う。
    bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 1), radius=1.0)
    body = bpy.context.active_object
    body.name = "TestBody"

    group_names = (
        "hip",
        "chest",
        "arm_l",
        "arm_r",
        "leg_l",
        "leg_r",
        "foot_l",
        "foot_r",
        "hand_l",
        "hand_r",
    )
    groups = {name: body.vertex_groups.new(name=name) for name in group_names}

    for vertex in body.data.vertices:
        x = vertex.co.x
        z = vertex.co.z
        index = vertex.index

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

    required = ("hip", "chest", "arm_l", "arm_r", "leg_l", "leg_r", "foot_l", "foot_r", "hand_l", "hand_r")
    for name in required:
        if not any(group.group == groups[name].index and group.weight > 0 for vertex in body.data.vertices for group in vertex.groups):
            raise RuntimeError(f"テスト用頂点グループが空です: {name}")

    return body


def find_generated_mesh(body: bpy.types.Object, before_names: set[str]) -> bpy.types.Object:
    new_meshes = [
        obj
        for obj in bpy.data.objects
        if obj.name not in before_names and obj != body and obj.type == "MESH"
    ]
    active = bpy.context.view_layer.objects.active
    if active in new_meshes:
        return active
    if len(new_meshes) == 1:
        return new_meshes[0]
    names = [obj.name for obj in new_meshes]
    raise RuntimeError(f"生成メッシュを一意に特定できません: {names}")


def remove_new_objects(before_names: set[str]) -> None:
    for obj in list(bpy.data.objects):
        if obj.name not in before_names:
            bpy.data.objects.remove(obj, do_unlink=True)


def run_test_suite(body: bpy.types.Object) -> dict[str, Any]:
    props = bpy.context.scene.adaptive_wear_generator_pro
    results: dict[str, Any] = {}
    overall_pass = True

    for wear_type in ("T_SHIRT", "PANTS", "BRA", "SOCKS", "GLOVES", "SKIRT"):
        test_name = f"Generate_{wear_type}_Test"
        before_names = {obj.name for obj in bpy.data.objects}
        generated_name = None
        error = None
        passed = False

        try:
            props.base_body = body
            props.wear_type = wear_type
            props.quality_level = "MEDIUM"
            props.auto_rigging = False
            if wear_type == "SKIRT":
                props.pleat_count = 12
                props.skirt_length = 0.5
            elif wear_type == "SOCKS":
                props.sock_length = 0.5
            elif wear_type == "GLOVES":
                props.glove_fingers = False

            bpy.ops.object.select_all(action="DESELECT")
            body.select_set(True)
            bpy.context.view_layer.objects.active = body

            result = bpy.ops.awgp.generate_wear()
            if "FINISHED" not in result:
                raise RuntimeError(f"生成オペレーターが失敗しました: {result}")

            generated = find_generated_mesh(body, before_names)
            if not generated.data.vertices or not generated.data.polygons:
                raise RuntimeError("生成メッシュに頂点または面がありません")

            generated_name = generated.name
            passed = True
            logger.info("PASS %s: %s", wear_type, generated_name)
        except Exception as exc:
            error = str(exc)
            overall_pass = False
            logger.error("FAIL %s: %s", wear_type, error)
            traceback.print_exc()
        finally:
            remove_new_objects(before_names)

        results[test_name] = {
            "passed": passed,
            "error": error,
            "generated_object": generated_name,
        }

    try:
        bpy.ops.object.select_all(action="DESELECT")
        body.select_set(True)
        bpy.context.view_layer.objects.active = body
        result = bpy.ops.awgp.diagnose_bones()
        passed = "FINISHED" in result
        error = None if passed else f"診断オペレーターが失敗しました: {result}"
    except Exception as exc:
        passed = False
        error = str(exc)
        traceback.print_exc()

    results["DiagnoseBones_Test"] = {"passed": passed, "error": error}
    if not passed:
        overall_pass = False
    results["overall_pass"] = overall_pass
    return results


def save_test_results(results: dict[str, Any], output_dir: str) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "basic_functionality_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# AdaptiveWear Generator Pro 基本機能テストレポート",
        "",
        f"Blenderバージョン: {bpy.app.version_string}",
        "",
    ]
    for name, result in results.items():
        if name == "overall_pass":
            continue
        status = "PASS" if result.get("passed") else "FAIL"
        lines.append(f"## {name}: {status}")
        if result.get("generated_object"):
            lines.append(f"生成オブジェクト: {result['generated_object']}")
        if result.get("error"):
            lines.append(f"エラー: {result['error']}")
        lines.append("")
    lines.append(f"総合結果: {'PASS' if results.get('overall_pass') else 'FAIL'}")
    (output / "basic_functionality_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    output_dir = "test-results/basic-functionality"
    for index, arg in enumerate(argv):
        if arg == "--output-dir" and index + 1 < len(argv):
            output_dir = argv[index + 1]

    body = setup_test_environment()
    results = run_test_suite(body)
    save_test_results(results, output_dir)
    raise SystemExit(0 if results["overall_pass"] else 1)


if __name__ == "__main__":
    main()
