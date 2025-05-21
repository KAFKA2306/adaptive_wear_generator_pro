from tests import helpers
helpers.setup_addon_import_path()
import pytest
import bpy # bpyモジュールをインポート
import os # osモジュールをインポート
from adaptive_wear_generator_pro.core.export_tools import export_to_fbx

def test_export_to_fbx_returns_true():
    # テスト用のオブジェクトを作成
    bpy.ops.mesh.primitive_cube_add(size=1.0, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    garment_obj = bpy.context.object

    try:
        # export_to_fbx 関数に実際のオブジェクトを渡す
        result = export_to_fbx(garment_obj, os.path.join(os.path.dirname(__file__), "dummy.fbx")) # 一時ファイルパスを生成
        assert result is True
    finally:
        # 作成したオブジェクトをクリーンアップ
        if garment_obj and garment_obj.name in bpy.data.objects:
            bpy.data.objects.remove(garment_obj, do_unlink=True)
        # エクスポートした一時ファイルを削除 (オプション)
        # import os
        # temp_fbx_path = os.path.join(os.path.dirname(__file__), "dummy.fbx")
        # if os.path.exists(temp_fbx_path):
        #     os.remove(temp_fbx_path)