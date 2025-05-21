import tests.helpers
helpers.setup_addon_import_path()
import sys
import unittest
import os

# 現在のスクリプトのディレクトリを取得
script_dir = os.path.dirname(os.path.abspath(__file__))
# プロジェクトのルートディレクトリ（adaptive_wear_generator_pro の親ディレクトリ）を計算
project_root = os.path.join(script_dir, os.pardir, os.pardir)

# プロジェクトルートを sys.path に追加
if project_root not in sys.path:
    sys.path.append(project_root)

# adaptive_wear_generator_pro ディレクトリを sys.path に追加
addon_root = os.path.join(script_dir, os.pardir)
if addon_root not in sys.path:
    sys.path.append(addon_root)

# テストスイートの構築

# テストスイートの構築
def get_test_suite():
    test_loader = unittest.TestLoader()
    # テストファイルが含まれるディレクトリを明示的に指定
    test_suite = test_loader.discover(script_dir, pattern='test_*.py')
    return test_suite

# テストの実行
if __name__ == "__main__":
    test_suite = get_test_suite()
    test_result = unittest.TextTestRunner().run(test_suite)
    # Blender終了時にエラー状態を返す
    sys.exit(not test_result.wasSuccessful())