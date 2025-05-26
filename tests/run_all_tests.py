import os
import subprocess
import sys

# テスト結果ディレクトリ
TEST_RESULTS_DIR = "test-results"

# テストリスト: (スクリプトパス, 出力ディレクトリ)
tests = [
    ("tests/run_pleats_quality_test.py", os.path.join(TEST_RESULTS_DIR, "pleats_quality")),
    ("tests/run_basic_functionality_test.py", os.path.join(TEST_RESULTS_DIR, "basic_functionality")),
    ("tests/run_mesh_integrity_test.py", os.path.join(TEST_RESULTS_DIR, "mesh_integrity")),
    ("tests/run_visual_regression_test.py", os.path.join(TEST_RESULTS_DIR, "visual_regression")),
]

def ensure_output_dirs_exist():
    """テスト結果ディレクトリと各テストの出力ディレクトリが存在することを確認する"""
    if not os.path.exists(TEST_RESULTS_DIR):
        print(f"'{TEST_RESULTS_DIR}' ディレクトリを作成します...")
        os.makedirs(TEST_RESULTS_DIR)

    for _, output_dir in tests:
        if not os.path.exists(output_dir):
            print(f"'{output_dir}' ディレクトリを作成します...")
            os.makedirs(output_dir)

def run_test(script_path, output_dir):
    """指定されたテストスクリプトを実行する"""
    print(f"\n--- テスト実行: {script_path} ---")
    # Blender コマンドを構築
    # Blender 実行ファイルのパスは環境によって異なる可能性があるため、
    # ここでは 'blender' コマンドが PATH に含まれていることを前提とするか、
    # ユーザーにパスを指定させる必要がある。
    # 一旦 'blender' で試す。
    command = [
        "blender",
        "--background",
        "--python", script_path,
        "--", # スクリプト引数とBlender引数を区切る
        "--output-dir", output_dir
    ]
    print(f"コマンド: {' '.join(command)}")

    try:
        # テストを実行し、標準出力と標準エラーを取得
        # テストを実行し、標準出力と標準エラーを取得
        # check=True を指定することで、コマンドがゼロ以外の終了コードを返した場合に CalledProcessError を発生させる
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("--- 標準出力 ---")
        print(result.stdout)
        print("--- 標準エラー ---")
        print(result.stderr)

        if result.returncode == 0:
            print(f"テスト成功: {script_path}")
            return True
        else:
            print(f"テスト失敗: {script_path} (終了コード: {result.returncode})")
            return False
    except FileNotFoundError:
        print("エラー: 'blender' コマンドが見つかりません。Blender が PATH に追加されているか確認してください。")
        print(f"テスト失敗: {script_path}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"テスト実行中にエラーが発生しました (終了コード: {e.returncode}):")
        print("--- 標準出力 ---")
        print(e.stdout)
        print("--- 標準エラー ---")
        print(e.stderr)
        print(f"テスト失敗: {script_path}")
        return False
    except Exception as e: # pylint: disable=broad-except
        # その他の予期しないエラー
        print(f"予期しないエラーが発生しました: {e}")
        print(f"テスト失敗: {script_path}")
        return False

def main():
    """メイン実行関数"""
    ensure_output_dirs_exist()

    successful_tests = 0
    failed_tests = 0

    for script_path, output_dir in tests:
        if run_test(script_path, output_dir):
            successful_tests += 1
        else:
            failed_tests += 1

    print("\n--- テストサマリー ---")
    print(f"成功: {successful_tests}")
    print(f"失敗: {failed_tests}")
    print(f"合計: {successful_tests + failed_tests}")
    print("--------------------")

    # 全て成功した場合は終了コード0、そうでなければ1を返す
    sys.exit(0 if failed_tests == 0 else 1)

if __name__ == "__main__":
    main()