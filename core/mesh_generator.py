import bpy
from adaptive_wear_generator_pro.services.logging_service import log_info, log_warning, log_error

# このファイル内の既存の関数 (例)
def find_vertex_group_by_keyword(obj, keywords):
    """指定されたキーワードに一致する頂点グループ名を見つける"""
    if not obj or obj.type != 'MESH':
        return []
    
    found_groups = []
    for keyword in keywords:
        for vg in obj.vertex_groups:
            if keyword.lower() in vg.name.lower():
                found_groups.append(vg.name)
    if not found_groups:
        log_warning(f"オブジェクト '{obj.name}' にキーワード '{keywords}' に一致する頂点グループが見つかりませんでした。")
    return list(set(found_groups)) # 重複を削除して返す

def create_underwear_pants_mesh(base_body, vg_names, tight_fit, thickness):
    """パンツメッシュを作成する (既存の関数の仮のシグネチャ)"""
    log_info(f"create_underwear_pants_mesh が呼び出されました: body={base_body.name if base_body else 'None'}, vg_names={vg_names}, tight_fit={tight_fit}, thickness={thickness}")
    # ダミーのメッシュオブジェクトを作成して返す
    bpy.ops.mesh.primitive_cube_add(size=0.5)
    pants_mesh = bpy.context.object
    pants_mesh.name = "Generated_Pants"
    log_info(f"ダミーのパンツメッシュ '{pants_mesh.name}' を作成しました。")
    return pants_mesh

def create_underwear_bra_mesh(base_body, vg_names, tight_fit, thickness):
    """ブラメッシュを作成する (既存の関数の仮のシグネチャ)"""
    log_info(f"create_underwear_bra_mesh が呼び出されました: body={base_body.name if base_body else 'None'}, vg_names={vg_names}, tight_fit={tight_fit}, thickness={thickness}")
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3)
    bra_mesh = bpy.context.object
    bra_mesh.name = "Generated_Bra"
    log_info(f"ダミーのブラメッシュ '{bra_mesh.name}' を作成しました。")
    return bra_mesh

def create_socks_mesh(base_body, vg_names, tight_fit, thickness, length):
    """靴下メッシュを作成する (既存の関数の仮のシグネチャ)"""
    log_info(f"create_socks_mesh が呼び出されました: body={base_body.name if base_body else 'None'}, vg_names={vg_names}, tight_fit={tight_fit}, thickness={thickness}, length={length}")
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=length)
    socks_mesh = bpy.context.object
    socks_mesh.name = "Generated_Socks"
    log_info(f"ダミーの靴下メッシュ '{socks_mesh.name}' を作成しました。")
    return socks_mesh

def create_gloves_mesh(base_body, vg_names, tight_fit, thickness, fingered):
    """手袋メッシュを作成する (既存の関数の仮のシグネチャ)"""
    log_info(f"create_gloves_mesh が呼び出されました: body={base_body.name if base_body else 'None'}, vg_names={vg_names}, tight_fit={tight_fit}, thickness={thickness}, fingered={fingered}")
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.25)
    gloves_mesh = bpy.context.object
    gloves_mesh.name = "Generated_Gloves"
    log_info(f"ダミーの手袋メッシュ '{gloves_mesh.name}' を作成しました。")
    return gloves_mesh

def create_swimsuit_onesie_mesh(base_body, vg_names, tight_fit, thickness):
    """ワンピース水着メッシュを作成する (既存の関数の仮のシグネチャ)"""
    log_info(f"create_swimsuit_onesie_mesh が呼び出されました: body={base_body.name if base_body else 'None'}, vg_names={vg_names}, tight_fit={tight_fit}, thickness={thickness}")
    bpy.ops.mesh.primitive_cube_add(size=0.6)
    onesie_mesh = bpy.context.object
    onesie_mesh.name = "Generated_Onesie"
    log_info(f"ダミーのワンピース水着メッシュ '{onesie_mesh.name}' を作成しました。")
    return onesie_mesh

def create_swimsuit_bikini_mesh(base_body, vg_names, tight_fit, thickness):
    """ビキニメッシュを作成する (既存の関数の仮のシグネチャ)"""
    log_info(f"create_swimsuit_bikini_mesh が呼び出されました: body={base_body.name if base_body else 'None'}, vg_names={vg_names}, tight_fit={tight_fit}, thickness={thickness}")
    # ビキニはトップとボトムの2つの部分で構成されることが多いので、2つのオブジェクトを生成
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 0.3))
    bikini_top = bpy.context.object
    bikini_top.name = "Generated_Bikini_Top"
    bpy.ops.mesh.primitive_cube_add(size=0.3, location=(0, 0, -0.3))
    bikini_bottom = bpy.context.object
    bikini_bottom.name = "Generated_Bikini_Bottom"
    # この例では、最後に作成されたオブジェクト (ボトム) を返す。
    # 実際には、複数のオブジェクトをリストで返すか、結合するかなどの処理が必要。
    log_info(f"ダミーのビキニメッシュ '{bikini_top.name}' と '{bikini_bottom.name}' を作成しました。")
    return bikini_bottom 

def create_tights_mesh(base_body, vg_names, tight_fit, thickness):
    """タイツメッシュを作成する (既存の関数の仮のシグネチャ)"""
    log_info(f"create_tights_mesh が呼び出されました: body={base_body.name if base_body else 'None'}, vg_names={vg_names}, tight_fit={tight_fit}, thickness={thickness}")
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=1.0)
    tights_mesh = bpy.context.object
    tights_mesh.name = "Generated_Tights"
    log_info(f"ダミーのタイツメッシュ '{tights_mesh.name}' を作成しました。")
    return tights_mesh

# --- 新しいプレースホルダー関数 ---
def generate_initial_wear_mesh(wear_type: str, context, additional_settings: dict = None) -> bpy.types.Object or None:
    """
    指定された wear_type に基づいて初期メッシュを生成する。
    additional_settings を使用して、特定の衣装タイプの生成を調整する。
    """
    if additional_settings is None:
        additional_settings = {} # ガード節: additional_settingsがNoneの場合、空の辞書で初期化
        
    log_info(f"generate_initial_wear_mesh が呼び出されました。wear_type: {wear_type}, additional_settings: {additional_settings}")
    obj = None

    try:
        if wear_type == "Pants":
            # 簡単なズボンの形状 (2つの円柱を組み合わせる)
            # 左足
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=16,
                radius=0.15,
                depth=0.8,
                enter_editmode=False,
                align='WORLD',
                location=(-0.15, 0, 0.4), # Y軸方向に少しずらす
                scale=(1, 1, 1)
            )
            left_leg = context.object
            left_leg.name = "Temp_LeftLeg"

            # 右足
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=16,
                radius=0.15,
                depth=0.8,
                enter_editmode=False,
                align='WORLD',
                location=(0.15, 0, 0.4), # Y軸方向に少しずらす
                scale=(1, 1, 1)
            )
            right_leg = context.object
            right_leg.name = "Temp_RightLeg"
            
            # 股部分の直方体
            bpy.ops.mesh.primitive_cube_add(
                size=1,
                enter_editmode=False,
                align='WORLD',
                location=(0, 0, 0.85), # 脚の上部に来るように調整
                scale=(0.35, 0.2, 0.1) # 幅、奥行き、高さ
            )
            crotch_cube = context.object
            crotch_cube.name = "Temp_Crotch"

            # 結合
            bpy.ops.object.select_all(action='DESELECT')
            left_leg.select_set(True)
            right_leg.select_set(True)
            crotch_cube.select_set(True)
            context.view_layer.objects.active = crotch_cube # 結合のベースオブジェクト
            bpy.ops.object.join()
            
            obj = context.object
            obj.name = "GeneratedPants"
            # 原点をジオメトリの中心に移動 (任意、フィット処理で調整されるため必須ではない)
            # bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            # obj.location = (0,0,0) # ワールド原点に再配置

            log_info(f"初期メッシュ '{obj.name}' を生成しました。")

        elif wear_type == "Bra":
            # 簡単なブラの形状 (2つの球を変形させて組み合わせる)
            # 左カップ
            bpy.ops.mesh.primitive_uv_sphere_add(
                segments=16,
                ring_count=8,
                radius=0.2,
                enter_editmode=False,
                align='WORLD',
                location=(-0.15, -0.05, 0.6), # 少し前、胸の位置
                scale=(1, 0.8, 0.6) # X, Y, Zスケールで潰す
            )
            left_cup = context.object
            left_cup.name = "Temp_LeftCup"
            # Y軸周りに少し回転
            left_cup.rotation_euler[1] = 0.2 # Y軸周りに回転

            # 右カップ
            bpy.ops.mesh.primitive_uv_sphere_add(
                segments=16,
                ring_count=8,
                radius=0.2,
                enter_editmode=False,
                align='WORLD',
                location=(0.15, -0.05, 0.6),
                scale=(1, 0.8, 0.6)
            )
            right_cup = context.object
            right_cup.name = "Temp_RightCup"
            right_cup.rotation_euler[1] = -0.2 # Y軸周りに回転

            # 結合 (任意、ここでは別々のままにしておくことも考えられる)
            # bpy.ops.object.select_all(action='DESELECT')
            # left_cup.select_set(True)
            # right_cup.select_set(True)
            # context.view_layer.objects.active = left_cup
            # bpy.ops.object.join()
            # obj = context.object
            # obj.name = "GeneratedBra"
            # この例では最後に作成された右カップを返す (結合しない場合)
            # 実際にはストラップなども考慮するが、ここではカップのみ
            
            # 簡単のため、結合せずに最後に作成されたものを返すか、あるいは片方だけを返す
            # もし結合するなら上記コメントアウトを解除
            # ここでは、より単純に1つのオブジェクトとして扱うため、1つのトーラスを変形させる
            bpy.ops.object.select_all(action='DESELECT')
            if left_cup: left_cup.select_set(True); bpy.ops.object.delete()
            if right_cup: right_cup.select_set(True); bpy.ops.object.delete()

            bpy.ops.mesh.primitive_torus_add(
                major_radius=0.25,
                minor_radius=0.08,
                major_segments=24,
                minor_segments=12,
                align='WORLD',
                location=(0, -0.05, 0.6) # やや前、胸の高さ
            )
            obj = context.object
            # X軸方向に潰し、Z軸方向に少し伸ばす
            obj.scale = (1.3, 0.7, 0.9)
            # X軸周りに少し傾ける
            obj.rotation_euler[0] = 0.3 # X軸周りに回転
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

            obj.name = "GeneratedBra"
            log_info(f"初期メッシュ '{obj.name}' を生成しました。")

        elif wear_type == "Socks":
            sock_length = additional_settings.get("sock_length", 0.5) # デフォルト値 0.5
            log_info(f"Socks generation: sock_length = {sock_length}")
            # 簡単な靴下の形状 (円柱を変形)
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=16,
                radius=0.08,
                depth=sock_length, # sock_length を使用
                enter_editmode=False,
                align='WORLD',
                location=(0, 0, sock_length / 2), # 位置も長さに応じて調整
                scale=(1, 1, 1)
            )
            obj = context.object
            obj.name = "GeneratedSocks"
            log_info(f"初期メッシュ '{obj.name}' を生成しました (長さ: {sock_length})。")

        elif wear_type == "Gloves":
            glove_fingers = additional_settings.get("glove_fingers", False) # デフォルト値 False
            log_info(f"Gloves generation: glove_fingers = {glove_fingers}")
            
            if glove_fingers:
                # 指あり手袋 (簡単な形状: 複数の小さな円柱を配置するなど)
                # ここでは、より複雑な形状の代わりに、ログ出力と基本的な形状で示す
                log_info("指あり手袋の生成を試みます (現在はプレースホルダー)。")
                # プレースホルダーとして、少し複雑な形状（例：細長い立方体をいくつか組み合わせる）
                # 手のひら部分
                bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0.3))
                palm = context.object
                palm.name = "Temp_Palm"
                palm.scale = (0.15, 0.05, 0.2) # X, Y, Z
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

                # 指のプレースホルダー (5本の指)
                finger_positions = [
                    (-0.06, 0.0, 0.5), (-0.03, 0.0, 0.52), (0.0, 0.0, 0.53),
                    (0.03, 0.0, 0.52), (0.06, 0.0, 0.5)
                ]
                fingers = []
                for i, pos in enumerate(finger_positions):
                    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.02, depth=0.15, location=pos)
                    finger = context.object
                    finger.name = f"Temp_Finger_{i+1}"
                    fingers.append(finger)
                
                # 手のひらと指を結合
                bpy.ops.object.select_all(action='DESELECT')
                palm.select_set(True)
                for f in fingers:
                    f.select_set(True)
                context.view_layer.objects.active = palm
                bpy.ops.object.join()
                obj = context.object
                obj.name = "GeneratedGloves_Fingered"

            else:
                # 指なし手袋 (ミトン形状: 1つの大きな形状)
                log_info("指なし手袋（ミトン）の生成を試みます。")
                bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0.3))
                obj = context.object
                obj.scale = (0.2, 0.3, 0.4) # ミトンらしい形にスケール
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                # 親指部分の簡単な追加
                bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.05, depth=0.1, location=(-0.1, 0.0, 0.35))
                thumb_placeholder = context.object
                thumb_placeholder.name = "Temp_Thumb"
                thumb_placeholder.rotation_euler[1] = 0.5 # Y軸周りに少し回転

                # ミトン本体と親指を結合
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                thumb_placeholder.select_set(True)
                context.view_layer.objects.active = obj
                bpy.ops.object.join()
                obj.name = "GeneratedGloves_Mitten"
            
            if obj:
                log_info(f"初期メッシュ '{obj.name}' を生成しました。")
            else:
                # このelseブロックは、上記のif/elseのどちらかでobjが設定されるため、通常は到達しない
                log_warning("手袋のメッシュ生成に失敗しました（予期せぬエラー）。")
                bpy.ops.mesh.primitive_cube_add(size=0.5) # フォールバック
                obj = context.object
                obj.name = "GeneratedGloves_Fallback"
                log_info(f"フォールバックメッシュ '{obj.name}' を生成しました。")

        else:
            log_warning(f"未対応の wear_type: {wear_type} または追加設定が未定義。汎用的な立方体を生成します。")
            bpy.ops.mesh.primitive_cube_add(
                size=0.5,
                enter_editmode=False,
                align='WORLD',
                location=(0, 0, 0),
                scale=(1,1,1)
            )
            obj = context.object
            obj.name = f"Generated_Unknown_{wear_type}"
            log_info(f"汎用メッシュ '{obj.name}' を生成しました。")
            # この場合、Noneを返すか、この汎用オブジェクトを返すかは仕様による
            # 要件では「None を返すか、汎用的な立方体などを生成」なので、ここでは生成したものを返す
        
        if obj:
            # 原点とスケールの確認
            obj.location = (0, 0, 0)
            obj.scale = (1, 1, 1)
            # 既存のトランスフォームを適用（特にスケールや回転をプリミティブ生成時に行った場合）
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            log_info(f"オブジェクト '{obj.name}' の原点を (0,0,0) に、スケールを (1,1,1) に設定し、トランスフォームを適用しました。")
            return obj
        else:
            # このパスは通常通らないはずだが、念のため
            log_warning(f"wear_type: {wear_type} のメッシュオブジェクトが生成されませんでした。")
            return None

    except Exception as e: # pylint: disable=broad-except
        log_error(f"generate_initial_wear_mesh でエラーが発生しました (wear_type: {wear_type}): {e}")
        # 作成途中のオブジェクトが残っている可能性があるので削除
        if obj and obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        # 選択されている可能性のある一時オブジェクトも削除
        if "Temp_LeftLeg" in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects["Temp_LeftLeg"], do_unlink=True)
        if "Temp_RightLeg" in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects["Temp_RightLeg"], do_unlink=True)
        if "Temp_Crotch" in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects["Temp_Crotch"], do_unlink=True)
        if "Temp_LeftCup" in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects["Temp_LeftCup"], do_unlink=True)
        if "Temp_RightCup" in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects["Temp_RightCup"], do_unlink=True)
        return None
