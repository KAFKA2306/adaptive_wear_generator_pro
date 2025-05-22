import bpy
import unittest
import mathutils

# テスト対象のアドオンが有効になっていることを確認
# 実際のテスト実行時には、Blender起動時にアドオンを有効化するスクリプトが必要になる場合があります。
# ここでは、アドオンが手動または他の手段で有効化されていることを前提とします。

class TestGenerateWearOperatorIntegration(unittest.TestCase):
    """
    AWG_OT_GenerateWear オペレーターの統合テストクラス
    """

    def setUp(self):
        """
        各テストメソッドの実行前に呼び出されるセットアップメソッド。
        テスト用の素体メッシュとアドオンプロパティの準備を行う。
        """
        self.test_objects = []  # テスト中に作成されたオブジェクトを追跡

        # シーンをクリーンアップ
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        self.test_objects = []

        # テスト用の素体メッシュを作成
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
        self.base_body = bpy.context.active_object
        self.base_body.name = "TestBody"
        self.test_objects.append(self.base_body.name)

        # アドオンのプロパティを取得
        self.props = bpy.context.scene.adaptive_wear_generator_pro

        # デフォルトプロパティ設定
        self.props.base_body = self.base_body
        self.props.wear_type = "Pants" # デフォルトの衣装タイプ
        self.props.thickness = 0.02
        self.props.tight_fit = False
        self.props.sock_length = 0.5 # Socks用デフォルト

        # オペレーター実行前の状態を保存（必要に応じて）
        self.initial_object_count = len(bpy.data.objects)


    def tearDown(self):
        """
        各テストメソッドの実行後に呼び出されるクリーンアップメソッド。
        生成されたオブジェクトや設定を元に戻す。
        """
        # テスト中に作成されたオブジェクトを削除
        objects_to_delete = [obj for obj in bpy.data.objects if obj.name in self.test_objects]
        if objects_to_delete:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects_to_delete:
                obj.select_set(True)
            bpy.ops.object.delete()

        # 他のクリーンアップ処理（プロパティリセットなど）
        # プロパティは setUp で毎回設定されるため、明示的なリセットは不要な場合もある

    def assert_operator_result(self, result, expected=None):
        """オペレーターの実行結果を検証するヘルパーメソッド"""
        if expected is None:
            expected = {'FINISHED'}
        self.assertEqual(result, expected)

    def assert_object_generated(self, base_name, fitted=True):
        """
        指定された名前のオブジェクトが生成されたことを確認するヘルパーメソッド。
        fitted=True の場合、"_Fitted" サフィックスが付いた名前を期待する。
        """
        expected_suffix = "_Fitted" if fitted else ""
        # オペレーターの実装により、素体名がオブジェクト名に含まれる
        expected_obj_name = f"{base_name}_{self.base_body.name}{expected_suffix}"

        generated_obj = bpy.data.objects.get(expected_obj_name)
        self.assertIsNotNone(generated_obj, f"オブジェクト '{expected_obj_name}' が生成されていません。")
        self.assertIn(generated_obj.name, bpy.data.objects.keys(), f"オブジェクト '{expected_obj_name}' が bpy.data.objects に存在しません。")
        if generated_obj and generated_obj.name not in self.test_objects:
            self.test_objects.append(generated_obj.name) # クリーンアップ対象に追加
        return generated_obj

    def test_basic_pants_generation(self):
        """基本的なパンツ生成フローのテスト"""
        self.props.wear_type = "Pants"
        self.props.thickness = 0.03
        self.props.tight_fit = True

        # オペレーター呼び出し
        result = bpy.ops.awg.generate_wear()
        self.assert_operator_result(result)

        # オブジェクト生成確認
        generated_pants = self.assert_object_generated("Pants", fitted=True)

        # アクティブオブジェクトと選択状態の確認
        self.assertEqual(bpy.context.active_object, generated_pants, "生成されたパンツがアクティブオブジェクトではありません。")
        self.assertIn(generated_pants, bpy.context.selected_objects, "生成されたパンツが選択されていません。")
        self.assertEqual(len(bpy.context.selected_objects), 1, "選択されているオブジェクトが1つではありません。")

        # 素体との差異確認
        self.assertNotEqual(generated_pants, self.base_body, "生成されたパンツが素体と同じオブジェクトです。")
        self.assertTrue(len(generated_pants.data.vertices) > 0, "生成されたパンツに頂点がありません。")

    def test_socks_generation(self):
        """Socks生成フローのテスト"""
        self.props.wear_type = "Socks"
        self.props.sock_length = 0.7
        self.props.thickness = 0.01
        self.props.tight_fit = False

        result = bpy.ops.awg.generate_wear()
        self.assert_operator_result(result)

        generated_socks = self.assert_object_generated("Socks", fitted=True)

        self.assertEqual(bpy.context.active_object, generated_socks)
        self.assertIn(generated_socks, bpy.context.selected_objects)

        # Socksの長さの検証 (バウンディングボックスのZサイズでおおまかに確認)
        # 素体のサイズが2なので、sock_length 0.7 は素体の高さの70%程度を期待
        # バウンディングボックスの計算
        bbox_corners = [mathutils.Vector(corner) for corner in generated_socks.bound_box]
        min_z = min(c.z for c in bbox_corners)
        max_z = max(c.z for c in bbox_corners)
        bbox_height = (max_z - min_z) * generated_socks.scale.z # オブジェクトのスケールを考慮

        # 素体の高さは2.0 (cube size=2)
        # sock_length は 0.0 (足首) から 1.0 (膝上) までの割合
        # 大まかな期待値。正確な値はメッシュ生成ロジックに依存する
        # ここでは、ある程度の高さがあることを確認する
        # 例えば、素体の高さの (sock_length * 0.5) 以上であることを期待 (係数は調整が必要)
        expected_min_height = self.base_body.dimensions.z * self.props.sock_length * 0.3
        self.assertGreater(bbox_height, expected_min_height,
                           f"Socksの高さ ({bbox_height:.3f}) が期待値 ({expected_min_height:.3f}) より小さいです。sock_length: {self.props.sock_length}")

    def test_no_base_body_selected(self):
        """素体が未選択の場合のテスト"""
        self.props.base_body = None # 素体を未選択状態にする

        # オペレーター呼び出し
        # このオペレーターは report を使ってエラーを通知し、CANCELLED を返すことを期待
        # 実際のオペレーターの実装によっては、例外を発生させるかもしれない
        # ここでは、CANCELLED を期待する
        # TODO: オペレーターが self.report を使用している場合、そのメッセージをキャプチャする方法が必要
        #       現状では、戻り値のみを確認
        initial_object_count = len(bpy.data.objects)
        result = bpy.ops.awg.generate_wear()

        # オペレーターがエラーを報告し、キャンセルされることを確認
        self.assert_operator_result(result, {'CANCELLED'})

        # 新しいオブジェクトが生成されていないことを確認
        final_object_count = len(bpy.data.objects)
        self.assertEqual(final_object_count, initial_object_count, "素体未選択にも関わらずオブジェクトが生成されました。")

    def test_invalid_wear_type_if_possible(self):
        """
        不正な衣装タイプが設定された場合のテスト。
        EnumPropertyなので通常はUI/APIレベルで不正値は設定できないが、
        もし何らかの方法で設定できた場合の挙動を確認（主に堅牢性テスト）。
        現状のプロパティ定義では、EnumProperty のため、直接不正な文字列を設定することは難しい。
        このテストは、将来的な変更や、もしEnum以外の方法でwear_typeが設定されるケースを想定。
        """
        # EnumProperty は通常、定義外の値を受け付けない。
        # bpy.context.scene.adaptive_wear_generator_pro_props.wear_type = "InvalidWearType"
        # のような代入はエラーになる。
        # そのため、このテストケースは現状では実行が難しいか、
        # オペレーター内部で wear_type の妥当性チェックを行っている場合のテストとなる。
        # ここでは、もしオペレーターが内部で wear_type を検証し、
        # 不正な場合に CANCELLED を返すことを期待するシナリオを想定。

        # このテストは、プロパティシステムが不正な値を防ぐため、
        # 実際にはトリガーしにくい。
        # もしオペレーターが独自に wear_type の文字列を解釈する部分があれば、そこでテスト可能。
        # 今回はスキップするか、コメントアウトしておく。
        self.skipTest("不正な衣装タイプの設定はEnumPropertyにより通常は不可能。オペレーター内部での追加検証があればテスト対象。")

        # 以下は、もし不正な値を設定できた場合の想定コード
        # self.props.wear_type = "THIS_IS_NOT_A_VALID_WEAR_TYPE"
        # initial_object_count = len(bpy.data.objects)
        # result = bpy.ops.awg.generate_wear()
        # self.assert_operator_result(result, {'CANCELLED'})
        # final_object_count = len(bpy.data.objects)
        # self.assertEqual(final_object_count, initial_object_count)


# Blender内でテストを実行するための標準的な方法
# 以下のコードをBlenderのPythonコンソールに貼り付けるか、
# スクリプトとして実行することでテストが実行されます。
#
# if __name__ == "__main__":
#     # unittest.main() は Blender のスクリプト実行環境では直接動作しないことがあるため、
#     # TestLoader と TextTestRunner を使用する
#     suite = unittest.TestLoader().loadTestsFromTestCase(TestGenerateWearOperatorIntegration)
#     bpy.ops.wm.call_menu(name="INFO_MT_console_toggle") # コンソールを開いて結果を見やすくする
#     unittest.TextTestRunner(verbosity=2).run(suite)
#
# 外部から `run_tests_in_blender.py` のようなスクリプトで実行する場合は、
# そのスクリプト内でこのテストファイルがインポートされ、実行されるように設定します。