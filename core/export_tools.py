import bpy
import os

def export_to_fbx(obj, filepath):
    """オブジェクトをFBXとしてエクスポート"""
    # 元の選択状態を保存
    original_selection = [o for o in bpy.context.selected_objects]
    active_obj = bpy.context.active_object

    # 全選択解除
    bpy.ops.object.select_all(action='DESELECT')

    # エクスポートするオブジェクトを選択
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    try:
        # 相対パスを絶対パスに変換（Blender 4.1ではパス処理が厳密化）
        abs_path = filepath
        if filepath.startswith("//"):
            abs_path = bpy.path.abspath(filepath)

        # ディレクトリがなければ作成
        dir_path = os.path.dirname(abs_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        # FBXエクスポート
        bpy.ops.export_scene.fbx(
            filepath=abs_path,
            use_selection=True,
            use_active_collection=False,
            use_mesh_modifiers=True,
            add_leaf_bones=False,
            bake_anim=False
        )
        return True

    except (RuntimeError, OSError) as e:
        print(f"FBXエクスポートエラー: {e}")
        return False

    finally:
        # 元の選択状態を復元
        bpy.ops.object.select_all(action='DESELECT')
        for o in original_selection:
            o.select_set(True)
        if active_obj:
            bpy.context.view_layer.objects.active = active_obj