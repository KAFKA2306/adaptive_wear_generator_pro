"""生成衣装をFBXへ書き出し、空のBlenderへ再読込して最低限の交換可能性を確認する。"""

import json
import math
import os
import sys
import traceback
from pathlib import Path
from typing import Any

import bpy

addon_root = Path(os.environ["BLENDER_ADDON_PATH"]) / "adaptive_wear_generator_pro"
if str(addon_root) not in sys.path:
    sys.path.append(str(addon_root))


def setup_body() -> bpy.types.Object:
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
        if z >= 0.20: groups["chest"].add([index], 1.0, "REPLACE")
        if -0.20 <= z < 0.25: groups["hip"].add([index], 1.0, "REPLACE")
        if -0.80 <= z < -0.15: groups["leg_r" if x >= 0 else "leg_l"].add([index], 1.0, "REPLACE")
        if z < -0.65: groups["foot_r" if x >= 0 else "foot_l"].add([index], 1.0, "REPLACE")
        if z >= 0.0 and abs(x) >= 0.25: groups["arm_r" if x >= 0 else "arm_l"].add([index], 1.0, "REPLACE")
        if z >= -0.15 and abs(x) >= 0.70: groups["hand_r" if x >= 0 else "hand_l"].add([index], 1.0, "REPLACE")
    return body


def generate(body: bpy.types.Object) -> bpy.types.Object:
    props = bpy.context.scene.adaptive_wear_generator_pro
    props.base_body = body
    props.wear_type = "T_SHIRT"
    props.quality_level = "MEDIUM"
    props.auto_rigging = False
    before = {obj.name for obj in bpy.data.objects}
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    result = bpy.ops.awgp.generate_wear()
    if "FINISHED" not in result:
        raise RuntimeError(f"生成失敗: {result}")
    created = [obj for obj in bpy.data.objects if obj.name not in before and obj != body and obj.type == "MESH"]
    if len(created) != 1:
        raise RuntimeError(f"生成メッシュを一意に特定できません: {[obj.name for obj in created]}")
    return created[0]


def finite_mesh(obj: bpy.types.Object) -> bool:
    return bool(obj.data.vertices and obj.data.polygons) and all(
        math.isfinite(value) for vertex in obj.data.vertices for value in vertex.co
    )


def run(output_dir: Path) -> dict[str, Any]:
    body = setup_body()
    garment = generate(body)
    before = {"vertices": len(garment.data.vertices), "polygons": len(garment.data.polygons)}
    if not finite_mesh(garment):
        raise RuntimeError("FBX書き出し前の生成メッシュが不正です")

    fbx_path = output_dir / "generated_t_shirt.fbx"
    bpy.ops.object.select_all(action="DESELECT")
    garment.select_set(True)
    bpy.context.view_layer.objects.active = garment
    bpy.ops.export_scene.fbx(
        filepath=str(fbx_path),
        use_selection=True,
        object_types={"MESH"},
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        bake_anim=False,
        axis_forward="-Z",
        axis_up="Y",
    )
    if not fbx_path.is_file() or fbx_path.stat().st_size == 0:
        raise RuntimeError("FBX成果物が生成されませんでした")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(fbx_path))
    imported = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if len(imported) != 1:
        raise RuntimeError(f"FBX再読込後のメッシュ数が1ではありません: {len(imported)}")
    obj = imported[0]
    after = {"vertices": len(obj.data.vertices), "polygons": len(obj.data.polygons)}
    checks = {
        "fbx_exists": fbx_path.is_file(),
        "fbx_size_bytes": fbx_path.stat().st_size,
        "imported_mesh_count": len(imported),
        "finite_coordinates": finite_mesh(obj),
        "vertex_count_preserved": before["vertices"] == after["vertices"],
        "polygon_count_preserved": before["polygons"] == after["polygons"],
    }
    return {"before": before, "after": after, "checks": checks, "overall_pass": all(v for k, v in checks.items() if k != "fbx_size_bytes")}


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    output_dir = Path("test-results/fbx-roundtrip")
    for index, arg in enumerate(argv):
        if arg == "--output-dir" and index + 1 < len(argv):
            output_dir = Path(argv[index + 1])
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        results = run(output_dir)
    except Exception as exc:
        traceback.print_exc()
        results = {"checks": {}, "issues": [str(exc)], "overall_pass": False}
    (output_dir / "fbx_roundtrip_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if results["overall_pass"] else 1)


if __name__ == "__main__":
    main()
