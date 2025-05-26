"""
基本的なアドオン機能テスト
GitHub Actions専用実行スクリプト
"""

import bpy
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
    from adaptive_wear_generator_pro import core_properties
    from adaptive_wear_generator_pro import core_operators
    from adaptive_wear_generator_pro import core_generators
    from adaptive_wear_generator_pro import core_utils
    from adaptive_wear_generator_pro import ui_panels

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
    logger.info("=== 基本機能テスト環境セットアップ開始 ===")
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
        # 実際のAWG Proの要件に合わせて調整が必要
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

        logger.info("=== 基本機能テスト環境セットアップ完了 ===")
        return sphere

    except Exception as e:
        logger.error(f"❌ テスト環境セットアップ失敗: {e}")
        traceback.print_exc()
        return None


def run_test_suite(test_body: bpy.types.Object) -> Dict[str, Any]:
    """基本機能テストスイート実行"""
    logger.info("=== 基本機能テストスイート開始 ===")
    results: Dict[str, Any] = {}
    overall_pass = True

    if not test_body:
        logger.error("❌ テスト用素体メッシュがありません。テストスイートをスキップします。")
        results["setup_failed"] = True
        return results

    props = bpy.context.scene.adaptive_wear_generator_pro

    # テストする衣装タイプのリスト
    wear_types_to_test = ["T_SHIRT", "PANTS", "BRA", "SOCKS", "GLOVES", "SKIRT"]

    for wear_type in wear_types_to_test:
        test_name = f"Generate_{wear_type}_Test"
        logger.info(f"--- {test_name} 開始 ---")
        test_passed = False
        error_message = None
        generated_object_name = None

        try:
            # プロパティ設定
            props.base_body = test_body
            props.wear_type = wear_type
            props.quality_level = 'MEDIUM' # 高速な品質レベルでテスト
            # 衣装タイプ固有のプロパティも設定が必要な場合あり
            if wear_type == 'SKIRT':
                props.pleat_count = 12
                props.skirt_length = 0.5
            elif wear_type == 'SOCKS':
                props.sock_length = 0.5
            elif wear_type == 'GLOVES':
                props.glove_fingers = False # ミトンタイプでテスト

            # 生成実行
            bpy.ops.object.select_all(action='DESELECT') # 念のため選択解除
            test_body.select_set(True) # 素体を選択
            bpy.context.view_layer.objects.active = test_body # 素体をアクティブに

            result = bpy.ops.awgp.generate_wear()

            if 'FINISHED' in result:
                # 生成されたオブジェクトを検索
                # リファクタリング後の命名規則: f"{props.base_body.name}_{self.wear_type}_AI" または f"{props.base_body.name}_skirt"
                expected_name_ai = f"{test_body.name}_{wear_type}_AI"
                expected_name_skirt = f"{test_body.name}_skirt"
                generated_obj = None
                if expected_name_ai in bpy.data.objects:
                    generated_obj = bpy.data.objects[expected_name_ai]
                elif expected_name_skirt in bpy.data.objects:
                    generated_obj = bpy.data.objects[expected_name_skirt]

                if generated_obj and generated_obj.type == 'MESH':
                    # 基本的なメッシュデータが存在するか確認
                    if len(generated_obj.data.vertices) > 0 and len(generated_obj.data.polygons) > 0:
                        test_passed = True
                        generated_object_name = generated_obj.name
                        logger.info(f"✅ {test_name} PASS: オブジェクト '{generated_obj.name}' が生成されました。")
                    else:
                        error_message = "生成されたメッシュに頂点または面がありません。"
                        logger.error(f"❌ {test_name} FAIL: {error_message}")
                else:
                    error_message = "生成されたオブジェクトが見つからないか、メッシュではありません。"
                    logger.error(f"❌ {test_name} FAIL: {error_message}")
            else:
                error_message = f"オペレーター実行結果が 'FINISHED' ではありません: {result}"
                logger.error(f"❌ {test_name} FAIL: {error_message}")

        except Exception as e:
            error_message = str(e)
            logger.error(f"❌ {test_name} FAIL: {error_message}")
            traceback.print_exc()

        results[test_name] = {
            "passed": test_passed,
            "error": error_message,
            "generated_object": generated_object_name
        }
        if not test_passed:
            overall_pass = False

        # 生成されたオブジェクトを削除して次のテストに備える (任意)
        if generated_object_name and generated_object_name in bpy.data.objects:
             bpy.data.objects.remove(bpy.data.objects[generated_object_name], do_unlink=True)
             logger.debug(f"生成オブジェクト '{generated_object_name}' を削除しました。")


    # ボーン診断テスト
    test_name = "DiagnoseBones_Test"
    logger.info(f"--- {test_name} 開始 ---")
    test_passed = False
    error_message = None
    try:
        # 診断オペレーター実行
        bpy.ops.object.select_all(action='DESELECT')
        test_body.select_set(True)
        bpy.context.view_layer.objects.active = test_body

        result = bpy.ops.awgp.diagnose_bones()

        if 'FINISHED' in result:
            test_passed = True
            logger.info(f"✅ {test_name} PASS: オペレーター実行完了。詳細はコンソールログを確認。")
        else:
            error_message = f"オペレーター実行結果が 'FINISHED' ではありません: {result}"
            logger.error(f"❌ {test_name} FAIL: {error_message}")

    except Exception as e:
        error_message = str(e)
        logger.error(f"❌ {test_name} FAIL: {error_message}")
        traceback.print_exc()

    results[test_name] = {
        "passed": test_passed,
        "error": error_message
    }
    if not test_passed:
        overall_pass = False


    logger.info("=== 基本機能テストスイート完了 ===")
    results["overall_pass"] = overall_pass
    return results


def save_test_results(results: Dict[str, Any], output_dir: str) -> None:
    """テスト結果保存"""
    logger.info(f"=== テスト結果保存開始: {output_dir} ===")
    try:
        os.makedirs(output_dir, exist_ok=True)

        # JSON結果保存
        json_path = Path(output_dir) / "basic_functionality_results.json"
        with open(json_path, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"✅ JSON結果保存完了: {json_path}")

        # レポート生成 (簡易)
        report_path = Path(output_dir) / "basic_functionality_report.md"
        with open(report_path, "w", encoding='utf-8') as f:
            f.write("# AdaptiveWear Pro 基本機能テストレポート\n\n")
            f.write(f"**実行時刻**: {bpy.app.build_commit_timestamp}\n")
            f.write(f"**Blenderバージョン**: {bpy.app.version_string}\n\n")
            f.write("## テスト結果詳細\n\n")

            for test_name, test_result in results.items():
                if test_name == "overall_pass" or test_name == "setup_failed":
                    continue
                status = "✅ PASS" if test_result.get("passed", False) else "❌ FAIL"
                f.write(f"### {test_name}: {status}\n")
                if test_result.get("error"):
                    f.write(f"エラー: {test_result['error']}\n")
                if test_result.get("generated_object"):
                    f.write(f"生成オブジェクト: {test_result['generated_object']}\n")
                f.write("\n")

            f.write(f"\n**総合結果**: {'✅ PASS' if results.get('overall_pass', False) else '❌ FAIL'}\n")

        logger.info(f"✅ レポート保存完了: {report_path}")

        logger.info("=== テスト結果保存完了 ===")

    except Exception as inner_e:
        logger.error(f"❌ テスト結果保存エラー: {str(inner_e)}")
        traceback.print_exc()


def main():
    """メイン実行関数"""
    try:
        logger.info("🚀 AdaptiveWear Pro 基本機能テスト開始")

        # コマンドライン引数解析
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        output_dir = "test-results/basic-functionality" # デフォルト出力ディレクトリ

        for i, arg in enumerate(argv):
            if arg == "--output-dir" and i + 1 < len(argv):
                output_dir = argv[i+1]
                logger.info(f"➡️ 出力ディレクトリ設定: {output_dir}")
            # 他の引数も必要に応じて解析

        # テスト環境セットアップ
        test_body = setup_test_environment()
        if test_body is None:
            logger.error("❌ テスト環境セットアップ失敗。テストを終了します。")
            sys.exit(1)

        # テストスイート実行
        test_results = run_test_suite(test_body)

        # テスト結果保存
        save_test_results(test_results, output_dir)

        # 総合結果に基づいて終了コードを設定
        if test_results.get("overall_pass", False):
            logger.info("✅ 基本機能テスト総合結果: PASS")
            sys.exit(0) # 成功
        else:
            logger.error("❌ 基本機能テスト総合結果: FAIL")
            sys.exit(1) # 失敗

    except Exception as main_e:
        logger.error(f"❌ テスト実行中に予期せぬエラーが発生しました: {str(main_e)}")
        traceback.print_exc()
        sys.exit(1) # 予期せぬエラーで失敗

# Blenderスクリプトとして実行される場合
if __name__ == "__main__":
    main()