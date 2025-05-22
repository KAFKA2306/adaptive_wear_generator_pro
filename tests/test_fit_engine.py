import bpy
import unittest
import mathutils # バウンディングボックスの計算などに使用

# テスト対象の関数をインポート
# 注意: Blenderアドオンのテストでは、パスの通し方に工夫が必要な場合があります。
# この例では、アドオンがBlenderにインストールされ、Pythonパスが通っていることを前提とします。
# 必要に応じて sys.path.append() などを使用してください。
from core.fit_engine import fit_wear_to_body

def get_mesh_dimensions(mesh_obj):
    """メッシュオブジェクトのバウンディングボックスから寸法を取得"""
    if not mesh_obj or mesh_obj.type != 'MESH':
        return mathutils.Vector((0,0,0))
    
    # オブジェクトのワールド行列を考慮してバウンディングボックスの頂点を計算
    world_matrix = mesh_obj.matrix_world
    bbox_corners = [world_matrix @ mathutils.Vector(corner) for corner in mesh_obj.bound_box]
    
    min_x = min(corner.x for corner in bbox_corners)
    max_x = max(corner.x for corner in bbox_corners)
    min_y = min(corner.y for corner in bbox_corners)
    max_y = max(corner.y for corner in bbox_corners)
    min_z = min(corner.z for corner in bbox_corners)
    max_z = max(corner.z for corner in bbox_corners)
    
    return mathutils.Vector((max_x - min_x, max_y - min_y, max_z - min_z))

def get_vertex_count(mesh_obj):
    """メッシュオブジェクトの頂点数を取得"""
    if mesh_obj and mesh_obj.type == 'MESH' and mesh_obj.data:
        return len(mesh_obj.data.vertices)
    return 0

class TestFitEngine(unittest.TestCase):

    def setUp(self):
        """各テストの前に実行されるセットアップ処理"""
        self.test_objects = [] # 作成したオブジェクトを追跡

        # 既存のオブジェクトを全て削除 (テスト環境をクリーンにするため)
        # bpy.ops.object.select_all(action='SELECT')
        # bpy.ops.object.delete()

        # 1. 素体メッシュの作成 (例: 立方体)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        self.base_body_obj = bpy.context.active_object
        self.base_body_obj.name = "TestBaseBody"
        self.test_objects.append(self.base_body_obj)

        # 2. 初期衣装メッシュの作成 (例: 平面を少し上に配置)
        bpy.ops.mesh.primitive_plane_add(size=0.8, location=(0, 0, 0.6))
        self.wear_obj_orig = bpy.context.active_object
        self.wear_obj_orig.name = "TestWear_Initial"
        self.test_objects.append(self.wear_obj_orig)
        
        # 初期状態の頂点数を記録
        self.initial_wear_vertex_count = get_vertex_count(self.wear_obj_orig)


    def tearDown(self):
        """各テストの後に実行されるクリーンアップ処理"""
        # 作成したテストオブジェクトを削除
        if self.test_objects:
            bpy.ops.object.select_all(action='DESELECT')
            for test_obj in self.test_objects:
                if test_obj and test_obj.name in bpy.data.objects: # オブジェクトが存在するか確認
                    bpy.data.objects[test_obj.name].select_set(True)
            bpy.ops.object.delete()
        
        # コレクションからも参照を削除 (必要な場合)
        # 例えば、特定のコレクションに追加していた場合など
        self.test_objects.clear()

    def _duplicate_wear_mesh(self, name_suffix=""):
        """テスト用に衣装メッシュを複製するヘルパー関数"""
        bpy.ops.object.select_all(action='DESELECT')
        self.wear_obj_orig.select_set(True)
        bpy.context.view_layer.objects.active = self.wear_obj_orig
        bpy.ops.object.duplicate()
        duplicated_obj = bpy.context.active_object
        duplicated_obj.name = f"TestWear_Duplicate_{name_suffix}"
        self.test_objects.append(duplicated_obj) # クリーンアップリストに追加
        return duplicated_obj

    # --- 正常系テストケース ---
    def test_basic_fit_processing(self):
        """基本的なフィット処理のテスト"""
        wear_mesh_to_fit = self._duplicate_wear_mesh("BasicFit")
        initial_verts = get_vertex_count(wear_mesh_to_fit)

        fitted_mesh = fit_wear_to_body(
            generated_mesh=wear_mesh_to_fit,
            base_body=self.base_body_obj,
            thickness=0.02,
            tight_fit=False,
            context=bpy.context
        )

        self.assertIsNotNone(fitted_mesh, "フィット処理後のメッシュが返されませんでした。")
        self.assertEqual(fitted_mesh.name, wear_mesh_to_fit.name, "返されたオブジェクト名が一致しません。")
        
        # モディファイア適用により頂点数が変化することを確認 (ソリッド化で増えるはず)
        final_verts = get_vertex_count(fitted_mesh)
        self.assertGreater(final_verts, initial_verts, "モディファイア適用後、頂点数が増加していません。")
        
        # モディファイアが適用済みであることを確認（リストが空になっている）
        self.assertEqual(len(fitted_mesh.modifiers), 0, "適用後もモディファイアが残っています。")


    def test_thickness_setting_reflected(self):
        """thickness 設定が反映されるかのテスト"""
        wear_mesh_thin = self._duplicate_wear_mesh("Thin")
        wear_mesh_thick = self._duplicate_wear_mesh("Thick")

        thickness_thin = 0.01
        thickness_thick = 0.05

        fitted_thin = fit_wear_to_body(
            generated_mesh=wear_mesh_thin,
            base_body=self.base_body_obj,
            thickness=thickness_thin,
            tight_fit=False,
            context=bpy.context
        )
        self.assertIsNotNone(fitted_thin)
        dims_thin = get_mesh_dimensions(fitted_thin)

        fitted_thick = fit_wear_to_body(
            generated_mesh=wear_mesh_thick,
            base_body=self.base_body_obj,
            thickness=thickness_thick,
            tight_fit=False,
            context=bpy.context
        )
        self.assertIsNotNone(fitted_thick)
        dims_thick = get_mesh_dimensions(fitted_thick)

        # 厚みが増すと、少なくともZ軸方向の寸法が大きくなることを期待
        # シュリンクラップの影響もあるため、単純比較は難しいが、傾向として確認
        # print(f"Thin dims: {dims_thin}, Thick dims: {dims_thick}")
        self.assertTrue(dims_thick.z > dims_thin.z or 
                        dims_thick.x > dims_thin.x or 
                        dims_thick.y > dims_thin.y,
                        "thickness が大きい方が、メッシュの寸法が大きくなっていません。")
        # より具体的に、ソリッド化の厚み分だけ寸法が増えることを期待できるが、
        # シュリンクラップの影響で形状が変わるため、単純な加算にはならない。
        # ここでは、厚い方が何らかの次元で大きくなることを確認する。


    def test_tight_fit_setting_reflected(self):
        """tight_fit 設定が反映されるかのテスト"""
        wear_mesh_tight = self._duplicate_wear_mesh("TightFit")
        wear_mesh_loose = self._duplicate_wear_mesh("LooseFit")

        # 比較のため、初期位置を少しずらしておく
        wear_mesh_tight.location.z += 0.1
        wear_mesh_loose.location.z += 0.1

        fitted_tight = fit_wear_to_body(
            generated_mesh=wear_mesh_tight,
            base_body=self.base_body_obj,
            thickness=0.01, # thicknessは一定
            tight_fit=True,
            context=bpy.context
        )
        self.assertIsNotNone(fitted_tight)
        # tight_fit=True の場合、メッシュが素体に近くなるはず
        # 例: メッシュのZ軸最小値が、tight_fit=False の場合より小さくなる（素体に近づく）
        # min_z_tight = min(v.co.z for v in fitted_tight.data.vertices) # 未使用のため削除


        fitted_loose = fit_wear_to_body(
            generated_mesh=wear_mesh_loose,
            base_body=self.base_body_obj,
            thickness=0.01, # thicknessは一定
            tight_fit=False,
            context=bpy.context
        )
        self.assertIsNotNone(fitted_loose)
        # min_z_loose = min(v.co.z for v in fitted_loose.data.vertices) # 未使用のため削除
        
        # print(f"Min Z Tight: {center_z_tight}, Min Z Loose: {center_z_loose}") # コメント内の変数名を修正
        # tight_fit=True の方がシュリンクラップのオフセットが小さいため、より素体に近づく。
        # ただし、ソリッド化の影響もあるため、単純な比較は難しい。
        # ここでは、tight_fit=True の方が、メッシュの平均的なZ位置が素体に近くなる（小さくなる）傾向を期待。
        # または、バウンディングボックスの中心のZ座標を比較する。
        center_z_tight = fitted_tight.bound_box[0][2] + (fitted_tight.bound_box[6][2] - fitted_tight.bound_box[0][2]) / 2
        center_z_loose = fitted_loose.bound_box[0][2] + (fitted_loose.bound_box[6][2] - fitted_loose.bound_box[0][2]) / 2
        
        # print(f"Center Z Tight: {center_z_tight}, Center Z Loose: {center_z_loose}")
        # tight_fit=True の方がオフセットが0に近いため、より素体に密着する。
        # シュリンクラップのターゲットがZ=0中心の立方体なので、
        # tight_fit=True の方が衣装のZ座標が0に近くなることを期待。
        # ただし、初期衣装をZ=0.6に置いているので、フィット後はZ=0.5 (素体の上面) 付近に来るはず。
        # tight_fit=True の方が、より Z=0.5 に近い値になることを期待。
        # オフセットが0.005ある場合(loose)は、Z=0.505付近になる。
        self.assertLess(abs(center_z_tight - 0.5), abs(center_z_loose - 0.5), 
                        "tight_fit=True の方が、素体表面により近くなっていません。")


    # --- 異常系・境界値テストケース ---
    def test_no_base_body(self):
        """素体オブジェクトが存在しない場合のテスト"""
        wear_mesh = self._duplicate_wear_mesh("NoBaseBody")
        fitted_mesh = fit_wear_to_body(
            generated_mesh=wear_mesh,
            base_body=None, # 素体なし
            thickness=0.02,
            tight_fit=False,
            context=bpy.context
        )
        self.assertIsNone(fitted_mesh, "素体がない場合、Noneが返されるべきです。")

    def test_no_generated_mesh(self):
        """初期衣装メッシュが存在しない場合のテスト"""
        fitted_mesh = fit_wear_to_body(
            generated_mesh=None, # 衣装なし
            base_body=self.base_body_obj,
            thickness=0.02,
            tight_fit=False,
            context=bpy.context
        )
        self.assertIsNone(fitted_mesh, "初期衣装がない場合、Noneが返されるべきです。")

    def test_invalid_generated_mesh_type(self):
        """初期衣装メッシュがメッシュでない場合のテスト"""
        bpy.ops.object.light_add(type='POINT', location=(2,2,2)) # Blender 4.xでは light_add
        non_mesh_obj = bpy.context.active_object
        non_mesh_obj.name = "TestNonMesh"
        self.test_objects.append(non_mesh_obj)

        fitted_mesh = fit_wear_to_body(
            generated_mesh=non_mesh_obj,
            base_body=self.base_body_obj,
            thickness=0.02,
            tight_fit=False,
            context=bpy.context
        )
        self.assertIsNone(fitted_mesh, "初期衣装がメッシュでない場合、Noneが返されるべきです。")


    def test_invalid_base_body_mesh_type(self):
        """素体メッシュがメッシュでない場合のテスト"""
        wear_mesh = self._duplicate_wear_mesh("InvalidBaseBodyType")
        bpy.ops.object.camera_add(location=(2,2,2))
        non_mesh_obj = bpy.context.active_object
        non_mesh_obj.name = "TestNonMeshBase"
        self.test_objects.append(non_mesh_obj)

        fitted_mesh = fit_wear_to_body(
            generated_mesh=wear_mesh,
            base_body=non_mesh_obj,
            thickness=0.02,
            tight_fit=False,
            context=bpy.context
        )
        self.assertIsNone(fitted_mesh, "素体がメッシュでない場合、Noneが返されるべきです。")


    def test_invalid_thickness_value(self):
        """不正な thickness 値（例: 負の値）のテスト"""
        wear_mesh = self._duplicate_wear_mesh("InvalidThickness")
        
        # 現在の fit_wear_to_body の実装では、thickness の値のバリデーションは
        # Solidifyモディファイア自体に委ねられている。
        # Solidifyモディファイアは負の厚みも許容するため、エラーにはならず、
        # オブジェクトが返されることを期待する。
        # 将来的にバリデーションが追加された場合は、このテストは修正が必要。
        fitted_mesh = fit_wear_to_body(
            generated_mesh=wear_mesh,
            base_body=self.base_body_obj,
            thickness=-0.1, # 不正な値（負の厚み）
            tight_fit=False,
            context=bpy.context
        )
        # ログにはエラーが出るかもしれないが、関数はオブジェクトを返す可能性がある
        self.assertIsNotNone(fitted_mesh, 
                             "不正なthicknessでも、モディファイアが処理できる範囲ならオブジェクトが返されることを期待。")
        # 実際に厚みが反転するなどの振る舞いをするかは、Solidifyモディファイアの仕様による。
        # ここでは、クラッシュしたりNoneを返したりしないことを確認する。
        self.assertEqual(len(fitted_mesh.modifiers), 0, "適用後もモディファイアが残っています。")


# Blender内でこのテストを実行するためのランナー部分
# 通常、Blenderのテキストエディタからこのスクリプトを実行するか、
# コマンドラインから `blender --background --python tests/test_fit_engine.py` のように実行します。
#
# unittest.main() を直接呼び出すと、Blenderの終了処理と競合することがあるため、
# 以下のようなラッパーを用意することが推奨されます。

def run_tests():
    """このファイル内のテストスイートを実行します。"""
    suite = unittest.TestSuite()
    # TestFitEngine クラスの全てのテストメソッドをスイートに追加
    suite.addTest(unittest.makeSuite(TestFitEngine))
    
    # テストランナーの準備
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    return result

if __name__ == "__main__":
    # Blenderのテキストエディタから実行された場合
    print("Blender Text Editorからテストを実行します...")
    
    # 既存のテスト用オブジェクトが残っている可能性があるのでクリア
    if "TestBaseBody" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["TestBaseBody"], do_unlink=True)
    if "TestWear_Initial" in bpy.data.objects: # 他のテスト実行で残っている可能性
        bpy.data.objects.remove(bpy.data.objects["TestWear_Initial"], do_unlink=True)
    
    # 複製されたオブジェクトもクリア (名前に "TestWear_Duplicate_" を含むものを検索)
    for obj in list(bpy.data.objects): # イテレート中に変更するためリストのコピーを使用
        if obj.name.startswith("TestWear_Duplicate_"):
            bpy.data.objects.remove(obj, do_unlink=True)
        if obj.name.startswith("TestNonMesh"):
            bpy.data.objects.remove(obj, do_unlink=True)


    test_result = run_tests()

    # テスト結果に基づいてBlenderを終了させる (CI環境などで有用)
    # if not test_result.wasSuccessful():
    #     bpy.ops.wm.quit_blender() # エラーがあったら終了
    # else:
    #     bpy.ops.wm.quit_blender() # 成功しても終了 (CI用)

    # 通常のテスト実行では、Blenderを終了させずに結果を確認できるようにする
    print(f"テスト完了: 実行数={test_result.testsRun}, 失敗数={len(test_result.failures)}, エラー数={len(test_result.errors)}")

    # 失敗やエラーがあった場合、詳細を表示
    if test_result.failures:
        print("\n--- 失敗したテスト ---")
        for test, traceback_text in test_result.failures:
            print(f"テスト: {test}")
            print(traceback_text)
    
    if test_result.errors:
        print("\n--- エラーが発生したテスト ---")
        for test, traceback_text in test_result.errors:
            print(f"テスト: {test}")
            print(traceback_text)

    # CI環境向け: 失敗時は非ゼロの終了コードを返す
    # (BlenderのPython環境から直接 sys.exit() を呼ぶとBlenderが不安定になることがあるため注意)
    # if not test_result.wasSuccessful():
    #     # ここで何らかの方法で失敗を外部に伝える (例: ファイルに書き出す)
    #     with open("test_failure.flag", "w") as f:
    #         f.write("failed")
    #     # bpy.ops.wm.quit_blender() # CIでは通常終了させる