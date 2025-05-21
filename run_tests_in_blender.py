import pytest
import sys
import os

# プロジェクトのルートディレクトリをsys.pathに追加
# BlenderのPython環境からアドオンモジュールをインポートできるようにするため
# プロジェクトのルートディレクトリをsys.pathに追加
# プロジェクトのルートディレクトリとテストディレクトリをsys.pathに追加
# BlenderのPython環境からアドオンモジュールおよびテストモジュールをインポートできるようにするため
project_root = os.path.dirname(os.path.abspath(__file__)) # run_tests_in_blender.pyがあるディレクトリ
tests_dir = os.path.join(project_root, "tests")

if project_root not in sys.path:
    sys.path.append(project_root)
if tests_dir not in sys.path:
    sys.path.append(tests_dir)

# pytestを実行
# Blenderのコマンドライン引数をpytestに渡さないように、sys.argvを操作する
original_argv = sys.argv
sys.argv = [original_argv[0], "--disable-warnings", "-q"] # ここにpytestのオプションを指定
exit_code = pytest.main()

# 元のsys.argvに戻す (お作法として)
sys.argv = original_argv

# Blenderを終了する際に、テストの終了コードを反映させる方法が必要だが、
# BlenderのPython APIから直接終了コードを制御するのは難しい場合がある。
# 一旦、スクリプトの実行自体は成功とみなし、pytestの出力で結果を確認する方針とする。
# もし必要であれば、後で終了コードを適切に扱う方法を検討する。

# ただし、execute_commandの成功/失敗判定はBlenderの終了コードに依存する可能性があるため、
# ここでは簡単なprintでテスト結果の概要を示すに留める。
if exit_code == 0:
    print("\n================================================= Test Summary =================================================")
    print("All tests passed.")
else:
    print("\n================================================= Test Summary =================================================")
    print(f"Tests failed with exit code {exit_code}.")

# テスト結果をファイルに書き出す
# テスト結果をファイルに書き出す (絶対パスを使用)
addon_dir = os.path.dirname(os.path.abspath(__file__))
test_results_file = os.path.join(addon_dir, "test_results.txt")
with open(test_results_file, "w", encoding="utf-8") as f:
    if exit_code == 0:
        f.write("All tests passed.\n")
    else:
        f.write(f"Tests failed with exit code {exit_code}.\n")

# Blenderを終了する（バックグラウンド実行の場合、スクリプト終了で自動終了するはずだが念のため）
# bpy.ops.wm.quit_blender() # バックグラウンド実行では不要または問題を起こす可能性あり