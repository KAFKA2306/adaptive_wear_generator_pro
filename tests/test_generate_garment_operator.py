from tests import helpers
helpers.setup_addon_import_path()
import bpy
from adaptive_wear_generator_pro.core.mesh_generator import AWGP_OT_GenerateGarment

def test_operator_registration_and_execution():
    # クラスの登録テスト
    try:
        bpy.utils.register_class(AWGP_OT_GenerateGarment)
        assert AWGP_OT_GenerateGarment.bl_idname == "awgp.generate_garment"
    finally:
        bpy.utils.unregister_class(AWGP_OT_GenerateGarment)

    # 実行テスト: ダミーのアクティブオブジェクトを設定して呼び出す
    dummy_body = bpy.data.objects.new("DummyBody", bpy.data.meshes.new("MeshBody"))
    bpy.context.collection.objects.link(dummy_body)
    bpy.context.view_layer.objects.active = dummy_body

    bpy.utils.register_class(AWGP_OT_GenerateGarment)
    op = bpy.ops.awgp.generate_garment()
    bpy.utils.unregister_class(AWGP_OT_GenerateGarment)
    # op が {'FINISHED'} を返すか確認
    assert 'FINISHED' in op