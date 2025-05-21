import bpy
from bpy.props import BoolProperty, FloatProperty

def get_vertex_group_names(body_obj):
    """メッシュから頂点グループ名のリストを取得する"""
    return [vg.name for vg in body_obj.vertex_groups]
def find_vertex_group_by_keyword(body_obj, keywords):
    """キーワードで頂点グループをフィルタリング"""
    found = []
    for vg in body_obj.vertex_groups:
        for kw in keywords:
            if kw.lower() in vg.name.lower():
                found.append(vg.name)
                break
    return found
def create_basic_garment_mesh(body_obj):
    """基本的なガーメントメッシュを作成"""
    mesh_data = bpy.data.meshes.new("mvp_garment_mesh")
    garment_obj = bpy.data.objects.new("MVP_Garment", mesh_data)
    bpy.context.collection.objects.link(garment_obj)
    return garment_obj

import bmesh

def create_underwear_pants_mesh(body_obj, vg_names):
    """パンツ形状のメッシュを生成 (頂点グループベース)"""
    # 頂点グループ「hip」または「腰」を検索
    vg = None
    for group in body_obj.vertex_groups:
        if "hip" in group.name.lower() or "腰" in group.name:
            vg = group
            break
    if vg is None:
        print("Error: 'hip' or '腰' vertex group not found on the base body.")
        return None

    # 素体メッシュをコピーして新しいオブジェクトを作成
    mesh = body_obj.data.copy()
    pants_obj = bpy.data.objects.new(body_obj.name + "_pants", mesh)
    bpy.context.collection.objects.link(pants_obj)

    # bmeshに変換して頂点グループウェイトで頂点をフィルタリング
    bm = bmesh.new()
    bm.from_mesh(mesh)
    deform = bm.verts.layers.deform.verify()

    # hipグループのウェイトが高い頂点だけ残す
    selected_verts = [v for v in bm.verts if vg.index in v[deform] and v[deform][vg.index] > 0.5]
    remove_verts = [v for v in bm.verts if v not in selected_verts]
    
    # 選択されていない頂点を削除
    if remove_verts:
        bmesh.ops.delete(bm, geom=remove_verts, context='VERTS')

    # 軽く押し出し
    # 削除後に頂点インデックスが変わる可能性があるため、selected_vertsリストを使う
    # ただし、bmesh.ops.deleteはジオメトリを削除するため、元のbm.vertsを直接操作する方が安全
    # ここではシンプルに全ての残った頂点を押し出す
    if bm.verts:
        # 法線方向への押し出しは、面がない状態だと難しい場合があるため、単純な移動で代用
        # TODO: 面を生成してから押し出す、またはより洗練された方法を検討
        for v in bm.verts:
             # v.co += v.normal * 0.01 # 面がないと法線が安定しないためコメントアウト
            pass # 一旦押し出し処理はスキップ

    # bmeshの変更をメッシュに反映
    bm.to_mesh(mesh)
    bm.free()

    # スムーズシェードを適用
    # オブジェクトがシーンに追加され、アクティブになっている必要がある
    bpy.context.view_layer.objects.active = pants_obj
    pants_obj.select_set(True)
    bpy.ops.object.shade_smooth()
    
    # 素体のモディファイアをコピー（ミラーモディファイアなど）
    for mod in body_obj.modifiers:
        new_mod = pants_obj.modifiers.new(name=mod.name, type=mod.type)
        for attr in dir(new_mod):
            if not attr.startswith('__') and attr not in ['type', 'name']:
                try:
                    value = getattr(mod, attr)
                    setattr(new_mod, attr, value)
                except AttributeError:
                    pass # 属性が存在しない場合はスキップ
                except (AttributeError, TypeError):
                    pass # 属性が存在しない場合や型が一致しない場合はスキップ
                except Exception as e: # その他の予期しないエラー
                    print(f"Warning: Could not copy modifier attribute {attr}: {e}")


    return pants_obj

def create_underwear_bra_mesh(body_obj):
    """ブラジャー形状のメッシュを生成 (頂点グループベース)"""
    # 頂点グループ「chest」「breast」「胸」などを検索
    bra_vgs = find_vertex_group_by_keyword(body_obj, ["chest", "breast", "胸"])

    if not bra_vgs:
        print("Error: No relevant vertex groups found on the base body for bra generation (e.g., 'chest', 'breast', '胸').")
        return None

    # 素体メッシュをコピーして新しいオブジェクトを作成
    mesh = body_obj.data.copy()
    bra_obj = bpy.data.objects.new(body_obj.name + "_bra", mesh)
    bpy.context.collection.objects.link(bra_obj)

    # bmeshに変換して頂点グループウェイトで頂点をフィルタリング
    bm = bmesh.new()
    bm.from_mesh(mesh)
    deform = bm.verts.layers.deform.verify()

    # 関連する頂点グループのウェイトが高い頂点だけ残す
    selected_verts = []
    for v in bm.verts:
        is_selected = False
        for vg_name in bra_vgs:
            vg_index = body_obj.vertex_groups[vg_name].index
            if vg_index in v[deform] and v[deform][vg_index] > 0.1: # ウェイト閾値を調整
                is_selected = True
                break
        if is_selected:
            selected_verts.append(v)

    remove_verts = [v for v in bm.verts if v not in selected_verts]

    # 選択されていない頂点を削除
    if remove_verts:
        # 削除前に面を削除して孤立した頂点を減らす（オプション）
        # bmesh.ops.delete(bm, geom=[f for f in bm.faces if any(v in remove_verts for v in f.verts)], context='FACES')
        bmesh.ops.delete(bm, geom=remove_verts, context='VERTS')

    # 軽く押し出し（今回はスキップ、必要に応じて実装）
    # if bm.verts:
    #     pass # 一旦押し出し処理はスキップ

    # bmeshの変更をメッシュに反映
    bm.to_mesh(mesh)
    bm.free()

    # スムーズシェードを適用
    # オブジェクトがシーンに追加され、アクティブになっている必要がある
    bpy.context.view_layer.objects.active = bra_obj
    bra_obj.select_set(True)
    bpy.ops.object.shade_smooth()

    # 素体のモディファイアをコピー（ミラーモディファイアなど）
    for mod in body_obj.modifiers:
        try:
            new_mod = bra_obj.modifiers.new(name=mod.name, type=mod.type)
            # 可能な限りプロパティをコピー
            for attr in dir(mod):
                if not attr.startswith('__') and attr not in ['type', 'name']:
                    try:
                        value = getattr(mod, attr)
                        # bpy.types.bpy_struct型のプロパティはコピーしない（参照になるため）
                        if not isinstance(value, bpy.types.bpy_struct):
                            setattr(new_mod, attr, value)
                    except (AttributeError, TypeError, ValueError):
                        # 属性が存在しない場合や型/値が一致しない場合はスキップ
                        pass
                    except Exception as e:
                        # その他の予期しないエラーをログ
                        print(f"Warning: Could not copy modifier attribute {attr} from {mod.name}: {e}")
        except Exception as e:
            print(f"Warning: Could not copy modifier {mod.name}: {e}")

    return bra_obj
def create_socks_mesh(body_obj, vg_names, length="ankle"):
    """靴下メッシュを生成（長さ指定可能）"""
    mesh_data = bpy.data.meshes.new(f"mvp_socks_{length}_mesh")
    socks_obj = bpy.data.objects.new(f"MVP_Socks_{length}", mesh_data)
    bpy.context.collection.objects.link(socks_obj)
    return socks_obj
def check_polygon_count(obj, max_count=10000):
    """メッシュのポリゴン数が上限以下かチェック"""
    if obj and obj.type == 'MESH':
        poly_count = len(obj.data.polygons)
        return poly_count <= max_count
    return True
class AWGP_OT_GenerateGarment(bpy.types.Operator):
    bl_idname = "awgp.generate_garment"
    bl_label = "Generate Garment"
    bl_description = "素体に基づき衣装を自動生成"
    bl_options = {'REGISTER', 'UNDO'}

    fit_tightly: BoolProperty(
        name="Tight Fit",
        description="体に密着するフィット感にする",
        default=True
    )

    thickness: FloatProperty(
        name="Thickness",
        description="衣装の厚み (mm)",
        default=2.0,
        min=0.1,
        max=10.0
    )

    def execute(self, context):
        body = context.active_object
        if not body or body.type != 'MESH':
            self.report({'ERROR'}, "メッシュオブジェクトを選択してください")
            return {'CANCELLED'}

        garment = create_basic_garment_mesh(body)

        if garment:
            from .fit_engine import fit_mesh_to_body
            fit_mesh_to_body(garment, body,
                            offset=0.001 if self.fit_tightly else 0.01,
                            thickness=self.thickness/1000)

            from .uv_tools import unwrap_uv
            unwrap_uv(garment)

            from .material_manager import apply_basic_material
            apply_basic_material(garment)

            self.report({'INFO'}, "衣装が生成されました")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "衣装の生成に失敗しました")
            return {'CANCELLED'}
