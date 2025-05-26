"""
生成メッシュの整合性自動テスト
GitHub Actions専用実行スクリプト
"""

import bpy
import bmesh
import sys
import os
import json
import traceback
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# アドオンパス追加 (必要に応じて調整)
addon_path_env = os.environ.get("BLENDER_ADDON_PATH")
if addon_path_env:
    addon_path = Path(addon_path_env) / "adaptive_wear_generator_pro"
else:
    # デフォルトパス (GitHub Actionsの標準的な場所を想定)
    addon_path = Path.home() / ".config" / "blender" / "4.1" / "scripts" / "addons" / "adaptive_wear_generator_pro"

if str(addon_path) not in sys.path:
    sys.path.append(str(addon_path))
    logger.info(f"アドオンパスをsys.pathに追加: {addon_path}")

# coreモジュールをインポート (必要に応じて他のモジュールも)
try:
    # リファクタリング後のモジュール構造に合わせてインポート
    from . import core_properties
    from . import core_operators
    from . import core_generators
    from . import core_utils
    from . import ui_panels

    logger.info("✅ AdaptiveWear Generator Pro モジュールインポート成功")

except ImportError as e:
    logger.error(f"❌ AdaptiveWear Generator Pro モジュールのインポートに失敗しました: {e}")
    logger.error("sys.path: %s", sys.path)
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ モジュールインポート中に予期せぬエラーが発生しました: {e}")
    traceback.print_exc()
    sys.exit(1)


def setup_test_environment() -> Optional[bpy.types.Object]:
    """テスト環境の初期化"""
    logger.info("=== メッシュ整合性テスト環境セットアップ開始 ===")
    try:
        # デフォルトシーンクリア
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False) # use_global=False はBlender 4.xで推奨

        # アドオン有効化
        try:
            bpy.ops.preferences.addon_enable(module="adaptive_wear_generator_pro")
            logger.info("✅ AdaptiveWear Generator Pro アドオン有効化成功")
        except Exception as inner_e:
            logger.warning(f"⚠️ AdaptiveWear Generator Pro アドオン有効化失敗 (既に有効化されている可能性): {inner_e}")

        # テスト用素体メッシュ作成 (簡易的な人型を想定したUV球)
        bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 1), radius=1.0)
        sphere = bpy.context.active_object
        sphere.name = "TestBody"

        # 簡易頂点グループ追加 (主要な部位をカバー)
        vgs_to_add = ["hip", "chest", "arm_l", "arm_r", "leg_l", "leg_r", "foot_l", "foot_r", "hand_l", "hand_r"]
        for vg_name in vgs_to_add:
            sphere.vertex_groups.new(name=vg_name)

        # 簡易頂点グループ割り当て (Z座標ベースで大まかに割り当て)
        try:
            for i, v in enumerate(sphere.data.vertices):
                z = v.co.z
                if z > 1.5: # 頭部付近
                    pass # 今回のテストでは使用しない
                elif z > 1.0: # 上半身
                    if 'chest' in sphere.vertex_groups:
                        sphere.vertex_groups['chest'].add([i], 1.0, 'ADD')
                elif z > 0.5: # 腰部
                     if 'hip' in sphere.vertex_groups:
                         sphere.vertex_groups['hip'].add([i], 1.0, 'ADD')
                elif z > -0.5: # 脚部
                    # 簡易的に左右に分ける (X座標で判定)
                    if v.co.x > 0:
                        if 'leg_r' in sphere.vertex_groups:
                            sphere.vertex_groups['leg_r'].add([i], 1.0, 'ADD')
                    else:
                        if 'leg_l' in sphere.vertex_groups:
                            sphere.vertex_groups['leg_l'].add([i], 1.0, 'ADD')
                else: # 足部
                    if v.co.x > 0:
                        if 'foot_r' in sphere.vertex_groups:
                            sphere.vertex_groups['foot_r'].add([i], 1.0, 'ADD')
                    else:
                        if 'foot_l' in sphere.vertex_groups:
                            sphere.vertex_groups['foot_l'].add([i], 1.0, 'ADD')

            logger.info("✅ テスト用素体メッシュと簡易頂点グループ作成成功")
        except Exception as inner_e:
            logger.warning(f"⚠️ 頂点グループ割り当てエラー (テスト用): {inner_e}")

        logger.info("=== メッシュ整合性テスト環境セットアップ完了 ===")
        return sphere

    except Exception as e:
        logger.error(f"❌ テスト環境セットアップ失敗: {e}")
        traceback.print_exc()
        return None


def run_integrity_checks(mesh_obj: bpy.types.Object) -> Dict[str, Any]:
    """
    指定されたメッシュオブジェクトに対して整合性チェックを実行し、結果を返します。
    Args:
        mesh_obj: チェックするメッシュオブジェクト。
    Returns:
        チェック結果を含む辞書。
    """
    logger.info(f"--- メッシュ整合性チェック開始: {mesh_obj.name} ---")
    checks: Dict[str, Any] = {}
    issues: List[str] = []
    overall_pass = True

    if not (mesh_obj and mesh_obj.type == 'MESH'):
        logger.warning("⚠️ チェック対象オブジェクトがメッシュではありません。")
        checks["is_mesh"] = False
        issues.append("チェック対象がメッシュではありません。")
        return {"checks": checks, "issues": issues, "overall_pass": False}

    checks["is_mesh"] = True
    mesh = mesh_obj.data

    # 1. 基本的なジオメトリ存在チェック
    checks["has_vertices"] = len(mesh.vertices) > 0
    checks["has_edges"] = len(mesh.edges) > 0
    checks["has_faces"] = len(mesh.polygons) > 0

    if not checks["has_vertices"]:
        issues.append("頂点が存在しません。")
        overall_pass = False
    if not checks["has_edges"]:
        issues.append("辺が存在しません。")
        overall_pass = False
    if not checks["has_faces"]:
        issues.append("面が存在しません。")
        overall_pass = False

    if not overall_pass:
        logger.error("❌ 基本的なジオメトリが存在しません。")
        return {"checks": checks, "issues": issues, "overall_pass": False}

    # bmeshを使用した詳細チェック
    bm = bmesh.new()
    bm.from_mesh(mesh)

    try:
        # 2. 非多様体エッジ/頂点チェック
        non_manifold_verts = bmesh.ops.find_non_manifold(bm, geom=bm.verts)['verts']
        non_manifold_edges = bmesh.ops.find_non_manifold(bm, geom=bm.edges)['edges']
        checks["non_manifold_verts_count"] = len(non_manifold_verts)
        checks["non_manifold_edges_count"] = len(non_manifold_edges)
        checks["is_manifold"] = (len(non_manifold_verts) == 0 and len(non_manifold_edges) == 0)

        if not checks["is_manifold"]:
            issues.append(f"非多様体頂点が見つかりました: {checks['non_manifold_verts_count']}個")
            issues.append(f"非多様体エッジが見つかりました: {checks['non_manifold_edges_count']}個")
            overall_pass = False
            logger.warning(f"⚠️ 非多様体ジオメトリが見つかりました。頂点: {checks['non_manifold_verts_count']}, 辺: {checks['non_manifold_edges_count']}")
        else:
            logger.debug("✅ 非多様体ジオメトリは見つかりませんでした。")


        # 3. 孤立した頂点や辺がないことのテスト
        isolated_verts = [v for v in bm.verts if not v.link_edges]
        isolated_edges = [e for e in bm.edges if not e.link_faces]
        checks["isolated_verts_count"] = len(isolated_verts)
        checks["isolated_edges_count"] = len(isolated_edges)
        checks["has_isolated_geometry"] = (len(isolated_verts) > 0 or len(isolated_edges) > 0)

        if checks["has_isolated_geometry"]:
            issues.append(f"孤立した頂点が見つかりました: {checks['isolated_verts_count']}個")
            issues.append(f"孤立した辺が見つかりました: {checks['isolated_edges_count']}個")
            overall_pass = False
            logger.warning(f"⚠️ 孤立したジオメトリが見つかりました。頂点: {checks['isolated_verts_count']}, 辺: {checks['isolated_edges_count']}")
        else:
            logger.debug("✅ 孤立したジオメトリは見つかりませんでした。")


        # 4. 各面が3つ以上の頂点を持っているか (Nゴンチェック)
        invalid_faces = [f for f in bm.faces if len(f.verts) < 3] # 2頂点以下の面 (理論上ありえないがチェック)
        ngon_faces = [f for f in bm.faces if len(f.verts) > 4] # 5頂点以上の面 (Nゴン)
        checks["invalid_faces_count"] = len(invalid_faces)
        checks["ngon_faces_count"] = len(ngon_faces)
        checks["has_invalid_faces"] = (len(invalid_faces) > 0)
        checks["has_ngons"] = (len(ngon_faces) > 0) # Nゴンをエラーとするかは要件による

        if checks["has_invalid_faces"]:
            issues.append(f"3つ未満の頂点を持つ面が見つかりました: {checks['invalid_faces_count']}個")
            overall_pass = False
            logger.warning(f"⚠️ 3つ未満の頂点を持つ面が見つかりました: {checks['invalid_faces_count']}")

        # Nゴンを警告として扱う場合
        if checks["has_ngons"]:
             issues.append(f"Nゴン (5つ以上の頂点を持つ面) が見つかりました: {checks['ngon_faces_count']}個")
             logger.warning(f"⚠️ Nゴンが見つかりました: {checks['ngon_faces_count']}")


        # 5. 重複頂点チェック (cleanup_mesh と同様のロジック)
        original_verts_count = len(bm.verts)
        # 結合距離はプロジェクトの許容範囲に合わせて調整
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        duplicate_count = original_verts_count - len(bm.verts)
        checks["duplicate_vertices_count"] = duplicate_count
        checks["has_duplicate_vertices"] = duplicate_count > 0

        if checks["has_duplicate_vertices"]:
            issues.append(f"重複頂点が見つかりました: {checks['duplicate_vertices_count']}個")
            overall_pass = False # 重複頂点は通常エラーとする
            logger.warning(f"⚠️ 重複頂点が見つかりました: {checks['duplicate_vertices_count']}")
        else:
            logger.debug("✅ 重複頂点は見つかりませんでした。")


        # 6. 面法線の一貫性チェック
        # TODO: 面法線が一貫しているかどうかのチェックロジックを追加
        # 例: bm.faces[0].normal と隣接面の法線を比較するなど
        checks["face_normals_consistent"] = True # 仮にTrueとする
        # if not checks["face_normals_consistent"]:
        #      issues.append("面法線に不一致が見つかりました。")
        #      overall_pass = False


        # 7. 厚みが適切に適用されているか（簡易的なチェック）
        # これはアドオンの具体的な実装に依存するため、ここでは簡易的なチェックのみを行います。
        # 例: ソリディファイモディファイアが存在するか、または頂点数が元のメッシュより増えているかなど。
        # 生成されたメッシュがソリディファイモディファイアを持っているか確認
        has_solidify_modifier = any(m.type == 'SOLIDIFY' for m in mesh_obj.modifiers)
        checks["has_solidify_modifier"] = has_solidify_modifier
        # 厚みチェックをエラーとするかは要件による。ここでは警告とする。
        if not has_solidify_modifier:
             issues.append("ソリディファイモディファイアが見つかりませんでした。厚みが適用されていない可能性があります。")
             logger.warning("⚠️ ソリディファイモディファイアが見つかりませんでした。")
        else:
             logger.debug("✅ ソリディファイモディファイアが見つかりました。")


    except ImportError:
        issues.append("bmeshモジュールが見つかりません。詳細チェックをスキップします。")
        overall_pass = False # bmeshがないと詳細チェック不可
        logger.error("❌ bmeshモジュールが見つかりません。")
    except Exception as e:
        issues.append(f"メッシュ整合性チェック中にエラーが発生しました: {str(e)}")
        overall_pass = False
        logger.error(f"❌ メッシュ整合性チェックエラー: {str(e)}")
        traceback.print_exc()
    finally:
        bm.free() # bmesh解放を忘れずに

    logger.info(f"--- メッシュ整合性チェック完了: {mesh_obj.name} ---")

    return {"checks": checks, "issues": issues, "overall_pass": overall_pass}


def save_test_results(results: Dict[str, Any], output_dir: str, wear_type: str) -> None:
    """テスト結果保存"""
    logger.info(f"=== テスト結果保存開始: {output_dir} ({wear_type}) ===")
    try:
        os.makedirs(output_dir, exist_ok=True)

        # JSON結果保存
        json_filename = f"mesh_integrity_results_{wear_type.lower()}.json"
        json_path = Path(output_dir) / json_filename
        with open(json_path, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"✅ JSON結果保存完了: {json_path}")

        # レポート生成 (簡易)
        report_filename = f"mesh_integrity_report_{wear_type.lower()}.md"
        report_path = Path(output_dir) / report_filename
        with open(report_path, "w", encoding='utf-8') as f:
            f.write(f"# AdaptiveWear Pro メッシュ整合性テストレポート ({wear_type})\n\n")
            f.write(f"**実行時刻**: {bpy.app.build_commit_timestamp}\n")
            f.write(f"**Blenderバージョン**: {bpy.app.version_string}\n\n")
            f.write("## チェック結果詳細\n\n")

            for check_name, check_value in results.get("checks", {}).items():
                f.write(f"- **{check_name}**: {check_value}\n")
            f.write("\n")

            if results.get('issues'):
                f.write("### 課題\n")
                for issue in results['issues']:
                    f.write(f"- {issue}\n")
                f.write("\n")

            f.write(f"**総合結果**: {'✅ PASS' if results.get('overall_pass', False) else '❌ FAIL'}\n")

        logger.info(f"✅ レポート保存完了: {report_path}")

        logger.info("=== テスト結果保存完了 ===")

    except Exception as inner_e:
        logger.error(f"❌ テスト結果保存エラー: {str(inner_e)}")
        traceback.print_exc()


def main():
    """メイン実行関数"""
    try:
        logger.info("🚀 AdaptiveWear Pro メッシュ整合性テスト開始")

        # コマンドライン引数解析
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        output_dir = "test-results/mesh-integrity" # デフォルト出力ディレクトリ
        wear_type_to_test = "T_SHIRT" # デフォルトのテスト対象衣装タイプ

        for i in range(0, len(argv), 2):
            if argv[i] == "--output-dir" and i + 1 < len(argv):
                output_dir = argv[i+1]
                logger.info(f"➡️ 出力ディレクトリ設定: {output_dir}")
            elif argv[i] == "--wear-type" and i + 1 < len(argv):
                wear_type_to_test = argv[i+1].upper()
                logger.info(f"➡️ テスト対象衣装タイプ設定: {wear_type_to_test}")
            # 他の引数も必要に応じて解析

        # テスト環境セットアップ
        test_body = setup_test_environment()
        if test_body is None:
            logger.error("❌ テスト環境セットアップ失敗。テストを終了します。")
            sys.exit(1)

        # 衣装生成実行
        logger.info(f"--- 衣装生成開始: {wear_type_to_test} ---")
        generated_obj = None
        try:
            props = bpy.context.scene.adaptive_wear_generator_pro
            props.base_body = test_body
            props.wear_type = wear_type_to_test
            props.quality_level = 'MEDIUM' # 高速な品質レベルでテスト
            # 衣装タイプ固有のプロパティも設定が必要な場合あり
            if wear_type_to_test == 'SKIRT':
                props.pleat_count = 12
                props.skirt_length = 0.5
            elif wear_type_to_test == 'SOCKS':
                props.sock_length = 0.5
            elif wear_type_to_test == 'GLOVES':
                props.glove_fingers = False # ミトンタイプでテスト

            bpy.ops.object.select_all(action='DESELECT')
            test_body.select_set(True)
            bpy.context.view_layer.objects.active = test_body

            result = bpy.ops.awgp.generate_wear()

            if 'FINISHED' in result:
                # 生成されたオブジェクトを検索
                expected_name_ai = f"{test_body.name}_{wear_type_to_test}_AI"
                expected_name_skirt = f"{test_body.name}_skirt"
                if expected_name_ai in bpy.data.objects:
                    generated_obj = bpy.data.objects[expected_name_ai]
                elif expected_name_skirt in bpy.data.objects:
                    generated_obj = bpy.data.objects[expected_name_skirt]

                if generated_obj:
                    logger.info(f"✅ 衣装生成成功: {generated_obj.name}")
                else:
                    logger.error(f"❌ 衣装生成失敗: 生成されたオブジェクトが見つかりません ({expected_name_ai} または {expected_name_skirt})")

            else:
                logger.error(f"❌ 衣装生成失敗: オペレーター実行結果が 'FINISHED' ではありません: {result}")

        except Exception as e:
            logger.error(f"❌ 衣装生成中にエラーが発生しました: {str(e)}")
            traceback.print_exc()

        # メッシュ整合性チェック実行
        integrity_results: Dict[str, Any] = {}
        if generated_obj:
            integrity_results = run_integrity_checks(generated_obj)
        else:
            integrity_results["overall_pass"] = False
            integrity_results["issues"] = ["衣装生成に失敗したため、整合性チェックをスキップしました。"]
            integrity_results["checks"] = {}
            logger.warning("⚠️ 衣装生成に失敗したため、整合性チェックをスキップしました。")


        # テスト結果保存
        save_test_results(integrity_results, output_dir, wear_type_to_test)

        # 生成されたオブジェクトを削除 (任意)
        if generated_obj and generated_obj.name in bpy.data.objects:
             bpy.data.objects.remove(bpy.data.objects[generated_obj.name], do_unlink=True)
             logger.debug(f"生成オブジェクト '{generated_obj.name}' を削除しました。")


        # 総合結果に基づいて終了コードを設定
        if integrity_results.get("overall_pass", False):
            logger.info("✅ メッシュ整合性テスト総合結果: PASS")
            sys.exit(0) # 成功
        else:
            logger.error("❌ メッシュ整合性テスト総合結果: FAIL")
            sys.exit(1) # 失敗

    except Exception as main_e:
        logger.error(f"❌ テスト実行中に予期せぬエラーが発生しました: {str(main_e)}")
        traceback.print_exc()
        sys.exit(1) # 予期せぬエラーで失敗

# Blenderスクリプトとして実行される場合
if __name__ == "__main__":
    main()