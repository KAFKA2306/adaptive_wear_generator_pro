import sys
import os
import unittest
import bpy

def setup_addon_import_path():
    """アドオンのインポートパスをセットアップする関数"""
    # アドオンのルートディレクトリをパスに追加
    addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if addon_root not in sys.path:
        sys.path.append(addon_root)

def setup_module_path():
    """モジュールのインポートパスをセットアップする関数"""
    # プロジェクトのルートディレクトリとテストディレクトリをsys.pathに追加
    project_root = os.path.dirname(os.path.abspath(__file__)) # helpers.pyがあるディレクトリ (testsディレクトリ)
    addon_root = os.path.dirname(project_root) # プロジェクトのルートディレクトリ

    if addon_root not in sys.path:
        sys.path.append(addon_root)
    if project_root not in sys.path:
        sys.path.append(project_root)


class BlenderTestCase(unittest.TestCase):
    """Blender環境で実行されるテストケースの基底クラス"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体のセットアップ"""
        # アドオンとモジュールのインポートパスを設定
        setup_addon_import_path()
        setup_module_path()


    def setUp(self):
        """各テストメソッドのセットアップ"""
        # テスト用のオブジェクトを作成（必要に応じて）
        bpy.ops.mesh.primitive_cube_add(size=1.0, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        self.test_obj = bpy.context.object

    def tearDown(self):
        """各テストメソッドのティアダウン"""
        # テスト用オブジェクトを削除
        if self.test_obj and self.test_obj.name in bpy.data.objects:
            bpy.data.objects.remove(self.test_obj, do_unlink=True)

        # シーン内の全てのオブジェクトを削除してクリーンな状態に戻す
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()


# 初期化時に自動的に実行
setup_addon_import_path()
setup_module_path()