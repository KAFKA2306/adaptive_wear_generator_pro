"""
プリーツスカート品質自動テスト
GitHub Actions専用実行スクリプト
"""

import bpy
import sys
import os
import json
import traceback
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# アドオンパス追加
# GitHub Actions上でのパスを想定。環境変数 BLENDER_ADDON_PATH が設定されている場合はそれを使用
addon_path_env = os.environ.get("BLENDER_ADDON_PATH")
if addon_path_env:
    addon_path = Path(addon_path_env) / "adaptive_wear_generator_pro"
else:
    # デフォルトパス (GitHub Actionsの標準的な場所を想定)
    addon_path = Path.home() / ".config" / "blender" / "4.1" / "scripts" / "addons" / "adaptive_wear_generator_pro"

if str(addon_path) not in sys.path:
    sys.path.append(str(addon_path))
    logger.info(f"アドオンパスをsys.pathに追加: {addon_path}")

# coreモジュールをインポート（アドオンパス追加後に実行）
try:
    # リファクタリング後のモジュール構造に合わせてインポート
    from . import core_properties
    from . import core_operators
    from . import core_generators
    from . import core_utils
    from . import ui_panels

    # テストで使用する特定の関数をインポート
    from core_utils import evaluate_pleats_geometry, find_vertex_groups_by_type
    # 他に必要な関数があればここに追加

    logger.info("✅ AdaptiveWear Generator Pro モジュールインポート成功")

except ImportError as e:
    logger.error(f"❌ AdaptiveWear Generator Pro モジュールのインポートに失敗しました: {e}")
    logger.error("sys.path: %s", sys.path)
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ モジュールインポート中に予期せぬエラーが発生しました: {e}")
    traceback.print_exc()
    sys.exit(1)


def setup_test_environment():
    """テスト環境の初期化"""
    logger.info("=== テスト環境セットアップ開始 ===")
    try:
        # デフォルトシーンクリア
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False) # use_global=False はBlender 4.xで推奨

        # アドオン有効化
        # GitHub Actionsのインストールステップで既に行われているはずですが、念のため
        try:
            bpy.ops.preferences.addon_enable(module="adaptive_wear_generator_pro")
            logger.info("✅ AdaptiveWear Generator Pro アドオン有効化成功")
        except Exception as inner_e:
            logger.warning(f"⚠️ AdaptiveWear Generator Pro アドオン有効化失敗 (既に有効化されている可能性): {inner_e}")
            # 有効化失敗は致命的ではない場合があるため、警告に留める

        # テスト用素体メッシュ作成 (UV球)
        bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 1))
        sphere = bpy.context.active_object
        sphere.name = "TestBody"

        # 簡易頂点グループ追加
        # 実際のAWG Proの要件に合わせて調整が必要
        # スカート生成には 'hip' または 'leg' 関連のグループが必要
        hip_vg = sphere.vertex_groups.new(name="hip")
        leg_l_vg = sphere.vertex_groups.new(name="leg_l")
        leg_r_vg = sphere.vertex_groups.new(name="leg_r")

        # 全頂点を腰部グループに割り当て（簡易）
        # 実際のAWG Proの頂点グループ割り当てロジックに合わせて調整が必要
        try:
            # 下半分の頂点を選択して割り当てる方がよりリアルだが、簡易テストなので全体に割り当て
            for i, v in enumerate(sphere.data.vertices):
                 # Z座標が中央より下にある頂点を簡易的に選択
                 if v.co.z < 1.0: # 球の中心が(0,0,1)なので、Z<1.0が下半分
                     hip_vg.add([i], 1.0, 'ADD')
            logger.info("✅ テスト用素体メッシュと簡易頂点グループ作成成功")
        except Exception as inner_e:
            logger.warning(f"⚠️ 頂点グループ割り当てエラー (テスト用): {inner_e}")
            # テスト続行のためエラーにはしないが警告

        return sphere

    except Exception as e:
        logger.error(f"❌ テスト環境セットアップ失敗: {e}")
        traceback.print_exc()
        return None


def run_pleats_generation_test(test_body):
    """プリーツスカート生成テスト"""
    logger.info("=== プリーツスカート生成テスト開始 ===")

    if not test_body:
        logger.error("❌ テスト用素体メッシュがありません。生成テストをスキップします。")
        return None

    # アドオンプロパティ設定
    try:
        props = bpy.context.scene.adaptive_wear_generator_pro
        props.base_body = test_body
        props.wear_type = 'SKIRT'
        props.quality_level = 'ULTIMATE' # 必要に応じて他の品質レベルもテスト
        props.pleat_count = 12 # テストするプリーツ数を指定
        props.pleat_depth = 0.05
        props.skirt_length = 0.6

        logger.info(f"⚙️ アドオンプロパティ設定: wear_type={props.wear_type}, pleat_count={props.pleat_count}")

    except AttributeError as inner_e:
        logger.error(f"❌ アドオンプロパティ設定エラー: {inner_e}")
        logger.error("AdaptiveWear Generator Pro のプロパティが見つからないか、登録されていません。")
        return None # 致命的なエラーなのでテスト続行不可
    except Exception as inner_e:
        logger.error(f"❌ アドオンプロパティ設定中に予期せぬエラー: {inner_e}")
        traceback.print_exc()
        return None # 致命的なエラーなのでテスト続行不可

    # 衣装生成実行
    try:
        # オペレーター実行前に素体を選択状態にする必要があるか確認 (通常は不要だが念のため)
        # core_operators.py の execute メソッド内で選択処理が行われることを期待
        # bpy.context.view_layer.objects.active = test_body
        # test_body.select_set(True)

        result = bpy.ops.awgp.generate_wear()
        if 'FINISHED' not in result:
            raise Exception(f"bpy.ops.awgp.generate_wear() 実行結果が 'FINISHED' ではありません: {result}")
        logger.info("✅ bpy.ops.awgp.generate_wear() 実行完了")

    except Exception as inner_e:
        logger.error(f"❌ 衣装生成実行エラー: {str(inner_e)}")
        traceback.print_exc()
        return None # 生成失敗時はNoneを返す

    # 生成されたオブジェクト検索
    skirt_obj = None
    # リファクタリング後の命名規則: f"{props.base_body.name}_skirt"
    expected_name = f"{test_body.name}_skirt"
    if expected_name in bpy.data.objects:
         skirt_obj = bpy.data.objects[expected_name]

    if not skirt_obj:
        logger.error(f"❌ 生成されたスカートオブジェクト '{expected_name}' が見つかりません")
        return None

    logger.info(f"✅ プリーツスカート生成成功: {skirt_obj.name}")
    return skirt_obj


def evaluate_quality_metrics(skirt_obj, expected_pleat_count):
    """品質メトリクス評価"""
    logger.info("=== 品質評価実行 ===")

    if skirt_obj is None:
        logger.warning("⚠️ 評価対象オブジェクトがありません。品質評価をスキップします。")
        return {"total_score": 0, "issues": ["評価対象オブジェクトなし"]}

    try:
        # core_utilsからインポートしたevaluate_pleats_geometry関数を使用
        quality_report = evaluate_pleats_geometry(skirt_obj, expected_pleat_count)

        logger.info(f"📊 品質スコア: {quality_report.get('total_score', 'N/A')}/100")

        # 詳細メトリクス
        metrics = {
            "total_score": quality_report.get('total_score', 0),
            # evaluate_pleats_geometry の戻り値のキーに合わせて調整
            "vertex_count": quality_report.get('vertex_count', 0),
            "face_count": quality_report.get('face_count', 0),
            "manifold_check": quality_report.get('manifold_check', False),
            "sharp_edge_count": quality_report.get('sharp_edge_count', 0),
            "actual_pleat_count_estimate": quality_report.get('actual_pleat_count_estimate', 0),
            "pleat_count_expected": expected_pleat_count,
            "issues": quality_report.get('messages', []), # messages キーを使用
            "timestamp": bpy.app.build_commit_timestamp
        }

        return metrics

    except NameError:
        logger.error("❌ 品質評価関数 evaluate_pleats_geometry が見つかりません。core_utilsからのインポートを確認してください。")
        return {"total_score": 0, "error": "evaluate_pleats_geometry関数未定義"}
    except Exception as inner_e:
        logger.error(f"❌ 品質評価エラー: {str(inner_e)}")
        traceback.print_exc()
        return {
            "total_score": 0,
            "error": str(inner_e),
            "vertex_count": len(skirt_obj.data.vertices) if skirt_obj else 0,
            "face_count": len(skirt_obj.data.polygons) if skirt_obj else 0
        }

def check_mesh_integrity(skirt_obj):
    """メッシュ整合性チェック"""
    logger.info("=== メッシュ整合性チェック ===")

    if skirt_obj is None:
        logger.warning("⚠️ 整合性チェック対象オブジェクトがありません。チェックをスキップします。")
        return {"integrity_score": 0, "issues": ["チェック対象オブジェクトなし"]}

    mesh = skirt_obj.data
    issues = []
    integrity_score = 100 # 初期スコア

    try:
        # 基本チェック
        if len(mesh.vertices) == 0:
            issues.append("頂点が存在しません")
            integrity_score -= 50

        if len(mesh.polygons) == 0:
            issues.append("面が存在しません")
            integrity_score -= 50

        if integrity_score <= 0: # 致命的な問題があればここで終了
            logger.error("❌ 致命的なメッシュ問題が見つかりました。")
            return {
                "integrity_score": max(0, integrity_score),
                "issues": issues,
                "vertex_count": len(mesh.vertices),
                "face_count": len(mesh.polygons)
            }

        # bmeshを使用した詳細チェック
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(mesh)

        # 非多様体エッジチェック
        # bmesh.edges.ensure_lookup_table() # 必要に応じてルックアップテーブル更新
        non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
        if non_manifold_edges:
            issues.append(f"非多様体エッジ: {len(non_manifold_edges)}個")
            integrity_score -= min(50, len(non_manifold_edges) * 5) # 個数に応じて減点

        # 重複頂点チェック (cleanup_mesh と同様のロジック)
        original_verts = len(bm.verts)
        # 結合距離はプロジェクトの許容範囲に合わせて調整
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        duplicate_count = original_verts - len(bm.verts)

        if duplicate_count > 0:
            issues.append(f"重複頂点: {duplicate_count}個")
            integrity_score -= min(30, duplicate_count * 2) # 個数に応じて減点

        # 面法線の一貫性チェック
        # TODO: 面法線が一貫しているかどうかのチェックロジックを追加
        # 例: bm.faces[0].normal と隣接面の法線を比較するなど

        bm.free() # bmesh解放を忘れずに

        # その他のメッシュ品質チェック（例: 鋭角な面、細すぎる面など）
        # TODO: 必要に応じて追加

    except ImportError:
        issues.append("bmeshモジュールが見つかりません。")
        integrity_score = 0 # bmeshがないと詳細チェック不可
        logger.error("❌ bmeshモジュールが見つかりません。")
    except Exception as inner_e:
        issues.append(f"メッシュ整合性チェックエラー: {str(inner_e)}")
        integrity_score = max(0, integrity_score - 30) # エラー発生で減点
        logger.error(f"❌ メッシュ整合性チェックエラー: {str(inner_e)}")
        traceback.print_exc()

    integrity_score = max(0, integrity_score) # スコアが負にならないように

    logger.info(f"🔍 メッシュ整合性スコア: {integrity_score}/100")
    if issues:
        logger.warning("整合性課題:")
        for issue in issues:
            logger.warning(f"  ⚠️ {issue}")

    return {
        "integrity_score": integrity_score,
        "issues": issues,
        "vertex_count": len(mesh.vertices) if skirt_obj else 0,
        "face_count": len(mesh.polygons) if skirt_obj else 0
    }

def save_test_results(quality_metrics, integrity_metrics, output_dir):
    """テスト結果保存"""
    logger.info(f"=== テスト結果保存開始: {output_dir} ===")
    try:
        os.makedirs(output_dir, exist_ok=True)

        results = {
            "test_type": "pleats_quality",
            "timestamp": bpy.app.build_commit_timestamp,
            "blender_version": bpy.app.version_string,
            "quality_metrics": quality_metrics,
            "integrity_metrics": integrity_metrics,
            # 合格基準: 品質スコア >= 70 かつ 整合性スコア >= 80
            "overall_pass": (
                quality_metrics.get("total_score", 0) >= 70 and
                integrity_metrics.get("integrity_score", 0) >= 80
            )
        }

        # JSON結果保存
        json_path = Path(output_dir) / "pleats_quality_results.json"
        with open(json_path, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"✅ JSON結果保存完了: {json_path}")

        # レポート生成
        report_path = Path(output_dir) / "quality_report.md"
        with open(report_path, "w", encoding='utf-8') as f:
            f.write("# プリーツスカート品質テストレポート\n\n")
            f.write(f"**実行時刻**: {results['timestamp']}\n")
            f.write(f"**Blenderバージョン**: {results['blender_version']}\n\n")
            f.write(f"## 品質スコア: {quality_metrics.get('total_score', 'N/A')}/100\n\n")
            f.write(f"## メッシュ整合性: {integrity_metrics.get('integrity_score', 'N/A')}/100\n\n")

            if quality_metrics.get('issues'):
                f.write("### 品質課題\n")
                for issue in quality_metrics['issues']:
                    f.write(f"- {issue}\n")

            if integrity_metrics.get('issues'):
                f.write("### 整合性課題\n")
                for issue in integrity_metrics['issues']:
                    f.write(f"- {issue}\n")

            f.write(f"\n**総合結果**: {'✅ PASS' if results['overall_pass'] else '❌ FAIL'}\n")
        logger.info(f"✅ レポート保存完了: {report_path}")

        logger.info("=== テスト結果保存完了 ===")
        return results

    except Exception as inner_e:
        logger.error(f"❌ テスト結果保存エラー: {str(inner_e)}")
        traceback.print_exc()
        return None


def main():
    """メイン実行関数"""
    try:
        logger.info("🚀 AdaptiveWear Pro プリーツスカート品質テスト開始")

        # コマンドライン引数解析
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        output_dir = "test-results/pleats-quality" # デフォルト出力ディレクトリ

        for i, arg in enumerate(argv):
            if arg == "--output-dir" and i + 1 < len(argv):
                output_dir = argv[i+1]
                logger.info(f"➡️ 出力ディレクトリ設定: {output_dir}")
            # 他の引数も必要に応じて解析
            # 例: --test-data-dir, --pleat-count など

        # テスト環境セットアップ
        test_body = setup_test_environment()
        if test_body is None:
            logger.error("❌ テスト環境セットアップ失敗。テストを終了します。")
            sys.exit(1)

        # プリーツスカート生成テスト実行
        skirt_obj = run_pleats_generation_test(test_body)

        # 品質メトリクス評価
        # run_pleats_generation_testがNoneを返す場合も考慮
        expected_pleat_count = bpy.context.scene.adaptive_wear_generator_pro.pleat_count if skirt_obj and hasattr(bpy.context.scene, 'adaptive_wear_generator_pro') else 12
        quality_metrics = evaluate_quality_metrics(skirt_obj, expected_pleat_count)

        # メッシュ整合性チェック
        integrity_metrics = check_mesh_integrity(skirt_obj)

        # テスト結果保存
        results = save_test_results(quality_metrics, integrity_metrics, output_dir)

        # 総合結果に基づいて終了コードを設定
        if results and results['overall_pass']:
            logger.info("✅ プリーツスカート品質テスト総合結果: PASS")
            sys.exit(0) # 成功
        else:
            logger.error("❌ プリーツスカート品質テスト総合結果: FAIL")
            sys.exit(1) # 失敗

    except Exception as main_e:
        logger.error(f"❌ テスト実行中に予期せぬエラーが発生しました: {str(main_e)}")
        traceback.print_exc()
        sys.exit(1) # 予期せぬエラーで失敗

# Blenderスクリプトとして実行される場合
if __name__ == "__main__":
    main()