import bpy
from adaptive_wear_generator_pro.services.logging_service import log_info, log_error # log_warning を削除

# このファイル内の既存の関数 (例)
def fit_mesh_to_body(garment_obj, body_obj, method='shrinkwrap', offset=0.01, smooth_iterations=2, apply_modifiers=True):
    """
    衣装メッシュを指定された素体メッシュにフィットさせる（既存の関数の仮のシグネチャ）。
    """
    log_info(f"fit_mesh_to_body が呼び出されました: garment='{garment_obj.name if garment_obj else 'None'}'"
             f", body='{body_obj.name if body_obj else 'None'}'"
             f", method='{method}', offset={offset}, smooth_iter={smooth_iterations}, apply_mods={apply_modifiers}")

    if not garment_obj or not body_obj:
        log_error("フィット処理には衣装オブジェクトと素体オブジェクトの両方が必要です。")
        return False

    if garment_obj.type != 'MESH' or body_obj.type != 'MESH':
        log_error("衣装と素体は両方ともメッシュオブジェクトである必要があります。")
        return False

    log_info(f"ダミーのフィット処理を実行します (実際には何もしません)。衣装: '{garment_obj.name}', 素体: '{body_obj.name}'")
    # 実際のフィット処理ロジックはここに実装される
    # 例: シュリンクラップモディファイアの追加と適用など

    # 仮に成功したとして True を返す
    return True


# --- 新しいプレースホルダー関数 ---
def fit_wear_to_body(generated_mesh: bpy.types.Object,
                     base_body: bpy.types.Object,
                     thickness: float,
                     tight_fit: bool,
                     context) -> bpy.types.Object or None:
    """
    生成された衣装メッシュを素体にフィットさせ、指定された設定を適用します。

    Args:
        generated_mesh (bpy.types.Object): フィットさせる生成された衣装メッシュ。
        base_body (bpy.types.Object): フィット先の素体メッシュ。
        thickness (float): 衣装の厚み。
        tight_fit (bool): True の場合、よりタイトにフィットさせます。
        context (bpy.types.Context): Blender のコンテキスト。

    Returns:
        bpy.types.Object or None: フィット処理後の衣装オブジェクト。エラーの場合は None。
    """
    log_info(f"fit_wear_to_body を開始: generated_mesh='{generated_mesh.name if generated_mesh else 'None'}'"
             f", base_body='{base_body.name if base_body else 'None'}'"
             f", thickness={thickness}, tight_fit={tight_fit}")
    log_info(f"fit_wear_to_body 関数開始: generated_mesh={generated_mesh.name if generated_mesh else 'None'}, base_body={base_body.name if base_body else 'None'}, thickness={thickness}, tight_fit={tight_fit}")

    if not generated_mesh or generated_mesh.type != 'MESH':
        log_error("生成されたメッシュが無効です。")
        return None
    if not base_body or base_body.type != 'MESH':
        log_error("素体メッシュが無効です。")
        return None

    # アクティブオブジェクトと選択状態を保存・復元するための準備
    original_active_object = context.view_layer.objects.active
    original_selected_objects = context.selected_objects[:]

    try:
        # generated_mesh をアクティブにし、選択状態にする
        context.view_layer.objects.active = generated_mesh
        bpy.ops.object.select_all(action='DESELECT')
        generated_mesh.select_set(True)

        # 1. シュリンクラップモディファイアの適用
        shrinkwrap_mod_name = "AWG_Shrinkwrap"
        shrinkwrap_mod = generated_mesh.modifiers.new(name=shrinkwrap_mod_name, type='SHRINKWRAP')
        shrinkwrap_mod.target = base_body
        shrinkwrap_mod.wrap_method = 'PROJECT'  # または 'NEAREST_SURFACEPOINT'
        # プロジェクト方向を調整 (法線方向が良い場合が多い)
        shrinkwrap_mod.project_axis = 'Z' # 必要に応じて変更
        shrinkwrap_mod.use_project_x = False
        shrinkwrap_mod.use_project_y = False
        shrinkwrap_mod.use_project_z = True # Z軸方向のみに投影する場合
        shrinkwrap_mod.use_negative_direction = True
        shrinkwrap_mod.use_positive_direction = True


        if tight_fit:
            shrinkwrap_mod.offset = 0.0  # タイトフィットの場合はオフセットを小さく
        else:
            shrinkwrap_mod.offset = 0.005  # 通常はある程度のオフセット

        log_info(f"シュリンクラップモディファイア '{shrinkwrap_mod_name}' を '{generated_mesh.name}' に追加しました。"
                 f" target='{base_body.name}', offset={shrinkwrap_mod.offset}")

        # 2. ソリッド化モディファイアの適用
        solidify_mod_name = "AWG_Solidify"
        solidify_mod = generated_mesh.modifiers.new(name=solidify_mod_name, type='SOLIDIFY')
        solidify_mod.thickness = thickness
        solidify_mod.offset = 1  # 外側に厚みを付ける

        log_info(f"ソリッド化モディファイア '{solidify_mod_name}' を '{generated_mesh.name}' に追加しました。"
                 f" thickness={solidify_mod.thickness}, offset={solidify_mod.offset}")

        # 3. モディファイアの適用
        log_info(f"'{generated_mesh.name}' のモディファイアを適用します...")

        # シュリンクラップモディファイアを適用
        try:
            bpy.ops.object.modifier_apply(modifier=shrinkwrap_mod_name)
            log_info(f"シュリンクラップモディファイア '{shrinkwrap_mod_name}' を適用しました。")
        except RuntimeError as e:
            log_error(f"シュリンクラップモディファイア '{shrinkwrap_mod_name}' の適用に失敗しました: {e}")
            # モディファイアが残っている可能性があるので削除を試みる
            if shrinkwrap_mod_name in generated_mesh.modifiers:
                generated_mesh.modifiers.remove(generated_mesh.modifiers[shrinkwrap_mod_name])
            if solidify_mod_name in generated_mesh.modifiers: # ソリッド化も失敗する可能性があるので削除
                generated_mesh.modifiers.remove(generated_mesh.modifiers[solidify_mod_name])
            return None

        # ソリッド化モディファイアを適用
        try:
            bpy.ops.object.modifier_apply(modifier=solidify_mod_name)
            log_info(f"ソリッド化モディファイア '{solidify_mod_name}' を適用しました。")
        except RuntimeError as e:
            log_error(f"ソリッド化モディファイア '{solidify_mod_name}' の適用に失敗しました: {e}")
            # モディファイアが残っている可能性があるので削除を試みる
            if solidify_mod_name in generated_mesh.modifiers:
                generated_mesh.modifiers.remove(generated_mesh.modifiers[solidify_mod_name])
            return None

        log_info(f"'{generated_mesh.name}' のフィット処理が正常に完了しました。")
        return generated_mesh

    except Exception as e: # pylint: disable=broad-except
        log_error(f"fit_wear_to_body で予期せぬエラーが発生しました: {e}")
        # エラー発生時、追加されたモディファイアを削除するクリーンアップ処理
        if 'shrinkwrap_mod' in locals() and shrinkwrap_mod_name in generated_mesh.modifiers:
            try:
                generated_mesh.modifiers.remove(shrinkwrap_mod)
                log_info(f"エラー発生のため、シュリンクラップモディファイア '{shrinkwrap_mod_name}' を削除しました。")
            except Exception as e_clean_shrink: # pylint: disable=broad-except
                log_error(f"シュリンクラップモディファイア '{shrinkwrap_mod_name}' の削除中にエラー: {e_clean_shrink}")

        if 'solidify_mod' in locals() and solidify_mod_name in generated_mesh.modifiers:
            try:
                generated_mesh.modifiers.remove(solidify_mod)
                log_info(f"エラー発生のため、ソリッド化モディファイア '{solidify_mod_name}' を削除しました。")
            except Exception as e_clean_solid: # pylint: disable=broad-except
                log_error(f"ソリッド化モディファイア '{solidify_mod_name}' の削除中にエラー: {e_clean_solid}")
        return None
    finally:
        # 元のアクティブオブジェクトと選択状態に戻す
        context.view_layer.objects.active = original_active_object
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selected_objects:
            obj.select_set(True)
        log_info("アクティブオブジェクトと選択状態を復元しました。")