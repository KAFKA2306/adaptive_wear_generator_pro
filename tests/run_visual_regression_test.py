"""
視覚的回帰テストスクリプト

このスクリプトはBlender内で実行され、AdaptiveWear Generator Proアドオンを使用して
特定の衣装を生成し、そのレンダリング画像を保存します。
生成された画像は、GitHub Actionsなどの外部プロセスによって基準画像と比較されます。
"""

import bpy
import sys
import os
import json
import traceback
import logging
from pathlib import Path
import argparse
import time
from typing import Dict, Any, List, Optional

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# アドオンパスを追加
# GitHub Actions環境やローカル環境に合わせて調整が必要になる場合があります。
# 環境変数 BLENDER_ADDON_PATH が設定されている場合はそれを使用
addon_name = "adaptive_wear_generator_pro"
addon_path_env = os.environ.get("BLENDER_ADDON_PATH")
if addon_path_env:
    addon_path = Path(addon_path_env) / addon_name
else:
    # デフォルトパス (GitHub Actionsの標準的な場所を想定)
    addon_path = Path.home() / ".config" / "blender" / f"{bpy.app.version[0]}.{bpy.app.version[1]}" / "scripts" / "addons" / addon_name

if str(addon_path) not in sys.path:
    sys.path.append(str(addon_path))
    logger.info(f"アドオンパスをsys.pathに追加: {addon_path}")

# coreモジュールをインポート
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


def setup_test_environment(wear_type: str) -> Optional[bpy.types.Object]:
    """
    テスト環境の初期化とシーンセットアップを行う。

    Args:
        wear_type: 生成する衣装のタイプ (例: 'T_SHIRT', 'SKIRT')

    Returns:
        セットアップに使用した素体オブジェクト、または失敗した場合はNone。
    """
    logger.info("=== 視覚的回帰テスト環境セットアップ開始 ===")
    try:
        # デフォルトシーンのクリア
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False) # use_global=False はBlender 4.xで推奨
        logger.debug("シーンをクリアしました。")

        # アドオン有効化
        try:
            bpy.ops.preferences.addon_enable(module="adaptive_wear_generator_pro")
            logger.info("✅ AdaptiveWear Generator Pro アドオン有効化成功")
        except Exception as inner_e:
            logger.warning(f"⚠️ AdaptiveWear Generator Pro アドオン有効化失敗 (既に有効化されている可能性): {inner_e}")

        # テスト用素体メッシュ作成 (簡易的な人型を想定したUV球)
        bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 1), radius=1.0)
        body_obj = bpy.context.active_object
        body_obj.name = "TestBody"
        logger.info(f"テスト用素体メッシュ '{body_obj.name}' を作成しました。")

        # 簡易頂点グループ追加 (主要な部位をカバー)
        vgs_to_add = ["hip", "chest", "arm_l", "arm_r", "leg_l", "leg_r", "foot_l", "foot_r", "hand_l", "hand_r"]
        for vg_name in vgs_to_add:
            body_obj.vertex_groups.new(name=vg_name)

        # 簡易頂点グループ割り当て (Z座標ベースで大まかに割り当て)
        try:
            for i, v in enumerate(body_obj.data.vertices):
                z = v.co.z
                if z > 1.5: # 頭部付近
                    pass # 今回のテストでは使用しない
                elif z > 1.0: # 上半身
                    if 'chest' in body_obj.vertex_groups:
                        body_obj.vertex_groups['chest'].add([i], 1.0, 'ADD')
                elif z > 0.5: # 腰部
                     if 'hip' in body_obj.vertex_groups:
                         body_obj.vertex_groups['hip'].add([i], 1.0, 'ADD')
                elif z > -0.5: # 脚部
                    # 簡易的に左右に分ける (X座標で判定)
                    if v.co.x > 0:
                        if 'leg_r' in body_obj.vertex_groups:
                            body_obj.vertex_groups['leg_r'].add([i], 1.0, 'ADD')
                    else:
                        if 'leg_l' in body_obj.vertex_groups:
                            body_obj.vertex_groups['leg_l'].add([i], 1.0, 'ADD')
                else: # 足部
                    if v.co.x > 0:
                        if 'foot_r' in body_obj.vertex_groups:
                            body_obj.vertex_groups['foot_r'].add([i], 1.0, 'ADD')
                    else:
                        if 'foot_l' in body_obj.vertex_groups:
                            body_obj.vertex_groups['foot_l'].add([i], 1.0, 'ADD')

            logger.debug("✅ テスト用素体メッシュと簡易頂点グループ作成成功")
        except Exception as inner_e:
            logger.warning(f"⚠️ 頂点グループ割り当てエラー (テスト用): {inner_e}")


        # カメラ設定
        bpy.ops.object.camera_add(location=(5, -5, 3), rotation=(0.9, 0.0, 0.78))
        camera_obj = bpy.context.object
        bpy.context.scene.camera = camera_obj
        logger.debug("テスト用カメラを設定しました。")

        # 照明設定
        bpy.ops.object.light_add(type='SUN', radius=1, align='WORLD', location=(0, 0, 10))
        light_obj = bpy.context.object
        light_obj.data.energy = 1.5
        logger.debug("テスト用照明を設定しました。")

        # レンダリング設定
        bpy.context.scene.render.engine = 'BLENDER_EEVEE' # EEVEEを使用
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.resolution_x = 256 # 小さめの解像度で高速化
        bpy.context.scene.render.resolution_y = 256
        bpy.context.scene.render.resolution_percentage = 100
        logger.debug("レンダリング設定を構成しました。")

        logger.info("=== 視覚的回帰テスト環境セットアップ完了 ===")
        return body_obj

    except Exception as e:
        logger.error(f"❌ テスト環境セットアップ中にエラーが発生しました: {e}")
        traceback.print_exc()
        return None


def generate_test_render(body_obj: bpy.types.Object, wear_type: str, output_path: Path) -> bool:
    """
    テスト用画像を生成する。

    Args:
        body_obj: 素体オブジェクト。
        wear_type: 生成する衣装のタイプ。
        output_path: レンダリング画像を保存するパス。

    Returns:
        生成とレンダリングが成功した場合はTrue、失敗した場合はFalse。
    """
    output_path_str = str(output_path)
    logger.info(f"=== テスト画像生成開始: {output_path_str} (衣装タイプ: {wear_type}) ===")
    generated_obj = None # 生成された衣装オブジェクトを保持する変数

    try:
        if not body_obj or not wear_type:
            logger.error("素体オブジェクトまたは衣装タイプが指定されていません。")
            return False

        # アドオンのプロパティを設定
        props = bpy.context.scene.adaptive_wear_generator_pro
        props.base_body = body_obj
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

        logger.debug(f"アドオンプロパティ設定: base_body='{props.base_body.name}', wear_type='{props.wear_type}'")

        # 衣装生成オペレーターを実行
        # オペレーター実行前に素体を選択状態にする
        bpy.ops.object.select_all(action='DESELECT')
        body_obj.select_set(True)
        bpy.context.view_layer.objects.active = body_obj

        result = bpy.ops.awgp.generate_wear()

        if 'FINISHED' in result:
            logger.debug(f"bpy.ops.awgp.generate_wear() 実行結果: {result}")
            # 生成されたオブジェクトを検索
            # リファクタリング後の命名規則: f"{props.base_body.name}_{self.wear_type}_AI" または f"{props.base_body.name}_skirt"
            expected_name_ai = f"{body_obj.name}_{wear_type}_AI"
            expected_name_skirt = f"{body_obj.name}_skirt"

            if expected_name_ai in bpy.data.objects:
                generated_obj = bpy.data.objects[expected_name_ai]
            elif expected_name_skirt in bpy.data.objects:
                generated_obj = bpy.data.objects[expected_name_skirt]

            if generated_obj and generated_obj.type == 'MESH':
                logger.info(f"✅ 衣装 '{wear_type}' 生成成功: {generated_obj.name}")
                # 生成されたオブジェクトを選択状態にする (レンダリングに直接は影響しないが、シーン確認用)
                bpy.ops.object.select_all(action='DESELECT')
                generated_obj.select_set(True)
                bpy.context.view_layer.objects.active = generated_obj
            else:
                logger.error(f"❌ 衣装生成失敗: 生成されたオブジェクトが見つかりません ({expected_name_ai} または {expected_name_skirt})")
                return False # 生成失敗

        else:
            logger.error(f"❌ 衣装生成失敗: オペレーター実行結果が 'FINISHED' ではありません: {result}")
            return False # オペレーター実行失敗

        # レンダリングパスを設定
        bpy.context.scene.render.filepath = output_path_str
        logger.debug(f"レンダリング出力パスを設定: {bpy.context.scene.render.filepath}")

        # レンダリング実行
        bpy.ops.render.render(write_still=True)
        logger.info("レンダリングを実行しました。")

        if output_path.exists():
            logger.info(f"✅ テスト画像生成完了: {output_path_str}")
            return True
        else:
            logger.error(f"❌ レンダリング画像ファイルが見つかりません: {output_path_str}")
            return False

    except Exception as e:
        logger.error(f"❌ テスト画像生成中にエラーが発生しました: {e}")
        traceback.print_exc()
        return False
    finally:
        # 生成されたオブジェクトを削除して次のテストに備える (任意)
        if generated_obj and generated_obj.name in bpy.data.objects:
             bpy.data.objects.remove(bpy.data.objects[generated_obj.name], do_unlink=True)
             logger.debug(f"生成オブジェクト '{generated_obj.name}' を削除しました。")


# TODO: 画像比較と差分保存のスタブ関数
# GitHub Actionsのreg-viz/reg-actionsアクションがこの比較を行うため、ここでは実装しない
# def compare_images(...): pass


def main():
    """メイン実行関数"""
    start_time = time.time()
    logger.info("🚀 AdaptiveWear Pro 視覚的回帰テスト開始")

    # コマンドライン引数解析
    # Blenderのsys.argvは特殊なので、'--'以降を解析する
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    parser = argparse.ArgumentParser(description="AdaptiveWear Pro 視覚的回帰テスト")
    parser.add_argument("--output-dir", type=str, default="test-renders/current",
                        help="レンダリング画像の出力ディレクトリ")
    parser.add_argument("--baseline-dir", type=str, default="test-renders/baseline",
                        help="基準画像が保存されているディレクトリ (比較は外部ツールが行う)")
    parser.add_argument("--diff-dir", type=str, default="test-renders/diff",
                        help="差分画像を保存するディレクトリ (比較は外部ツールが行う)")
    # テストする衣装タイプを引数で指定できるようにする (複数指定可能)
    parser.add_argument("--wear-types", nargs='+', default=["T_SHIRT", "SKIRT"],
                        help="テストする衣装タイプのリスト (例: T_SHIRT PANTS SKIRT)")


    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    # baseline_dir, diff_dir は GitHub Actions が比較を行うため、このスクリプト内では主にパスの構築に使用
    baseline_dir = Path(args.baseline_dir)
    diff_dir = Path(args.diff_dir)
    wear_types_to_test = [wt.upper() for wt in args.wear_types] # 大文字に変換

    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(diff_dir, exist_ok=True) # 差分ディレクトリも作成 (外部ツール用)
    logger.info(f"出力ディレクトリ: {output_dir}")
    logger.info(f"テスト対象衣装タイプ: {wear_types_to_test}")


    all_tests_passed = True
    test_results: Dict[str, bool] = {} # 各テストケースの成否を記録

    for wear_type in wear_types_to_test:
        test_name = f"{wear_type.lower()}_default" # テストケース名 (例: t_shirt_default)
        logger.info(f"\n--- テストケース開始: {test_name} (衣装タイプ: {wear_type}) ---")

        # テスト環境セットアップ
        body_obj = setup_test_environment(wear_type)
        if body_obj is None:
            logger.error(f"テストケース '{test_name}' のセットアップに失敗しました。")
            test_results[test_name] = False
            all_tests_passed = False
            continue # 次のテストケースへ

        # テスト画像生成
        test_image_path = output_dir / f"{test_name}.png"
        image_generated = generate_test_render(body_obj, wear_type, test_image_path)

        test_results[test_name] = image_generated
        if not image_generated:
            all_tests_passed = False

        # TODO: GitHub Actionsが比較を行うため、ここでは比較はスキップ
        # 基準画像パスの例: baseline_dir / f"{test_name}.png"
        # 差分画像パスの例: diff_dir / f"{test_name}_diff.png"

        logger.info(f"--- テストケース完了: {test_name} ---")

    # テスト結果のサマリーをJSONファイルに保存 (任意)
    results_summary_path = output_dir / "visual_regression_summary.json"
    try:
        with open(results_summary_path, "w", encoding='utf-8') as f:
            json.dump(test_results, f, indent=2)
        logger.info(f"✅ テスト結果サマリー保存完了: {results_summary_path}")
    except Exception as e:
        logger.error(f"❌ テスト結果サマリー保存エラー: {e}")


    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"\n🚀 AdaptiveWear Pro 視覚的回帰テスト終了 (所要時間: {duration:.2f}秒)")

    # GitHub Actionsのreg-viz/reg-actionsアクションがテスト結果を判定するため、
    # ここでは画像生成の成否に基づいて終了コードを設定する。
    # 複数のテストケースがある場合、全て成功した場合のみ終了コード0とする。
    if all_tests_passed:
        logger.info("✅ 全てのテスト画像生成が成功しました。")
        sys.exit(0) # 成功
    else:
        logger.error("❌ 一部または全てのテスト画像生成が失敗しました。")
        sys.exit(1) # 失敗


# Blenderスクリプトとして実行される場合
# Blenderのコマンドラインから実行する際は、以下のようにします。
# blender -b -P run_visual_regression_test.py -- --output-dir /path/to/output --wear-types T_SHIRT SKIRT
if __name__ == "__main__":
    main()