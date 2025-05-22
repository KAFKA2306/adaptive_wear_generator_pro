import bpy
import json
import os # os.path を使用するため

class AWG_PT_MainPanel(bpy.types.Panel):
    """AdaptiveWear Generator Pro メインパネル"""
    bl_label = "AdaptiveWear Generator"
    bl_idname = "AWG_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AdaptiveWear" # タブのカテゴリ名

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.adaptive_wear_generator_pro # プロパティグループを取得

        # --- 基本設定 ---
        box_base = layout.box()
        box_base.label(text="基本設定", icon='OBJECT_DATA')
        row = box_base.row()
        row.prop(props, "base_body")

        row = box_base.row()
        row.prop(props, "wear_type")

        # --- 追加設定 (衣装タイプに連動) ---
        addon_prefs = context.preferences.addons.get(__package__.split('.')[0], None)
        if addon_prefs:
            presets_dir = os.path.join(os.path.dirname(addon_prefs.filepath), "presets")
            wear_types_file = os.path.join(presets_dir, "wear_types.json")

            additional_props_to_display = []
            if os.path.exists(wear_types_file):
                try:
                    with open(wear_types_file, 'r', encoding='utf-8') as f:
                        wear_types_data = json.load(f)
                    
                    current_wear_type_id = props.wear_type
                    for wear_type_info in wear_types_data:
                        if wear_type_info.get("id") == current_wear_type_id:
                            additional_props_to_display = wear_type_info.get("additional_props", [])
                            break
                except json.JSONDecodeError:
                    layout.label(text="Error: wear_types.json is corrupted.", icon='ERROR')
                except Exception as e: # pylint: disable=broad-except
                    layout.label(text=f"Error loading wear_types.json: {e}", icon='ERROR')


            if additional_props_to_display:
                box_additional = layout.box()
                box_additional.label(text="追加設定", icon='SETTINGS')
                for prop_name in additional_props_to_display:
                    if hasattr(props, prop_name):
                        box_additional.prop(props, prop_name)
                    else:
                        # 念のため、プロパティが存在しない場合のエラー表示
                        box_additional.label(text=f"プロパティ '{prop_name}' が見つかりません。", icon='ERROR')
            elif props.wear_type: # wear_type が選択されているが、追加プロパティがない場合
                # 必要であれば「追加設定はありません」などのメッセージを表示
                # layout.label(text="追加設定はありません。")
                pass


        # --- フィット設定 ---
        box_fit = layout.box()
        box_fit.label(text="フィット設定", icon='MOD_CLOTH') # アイコン例
        row = box_fit.row()
        row.prop(props, "tight_fit")
        row = box_fit.row()
        row.prop(props, "thickness")

        # --- 衣装生成ボタン ---
        layout.separator() # スペーサー
        row = layout.row(align=True)
        row.scale_y = 1.5 # ボタンを少し大きくする
        # オペレーターIDは仮のものを指定
        row.operator("awg.generate_wear", text="Generate Wear", icon='PLAY')


def register():
    try:
        # 既に登録されている場合に備えて、一度登録解除を試みる
        bpy.utils.unregister_class(AWG_PT_MainPanel)
    except RuntimeError:
        pass # まだ登録されていなければ何もしない
    bpy.utils.register_class(AWG_PT_MainPanel)

def unregister():
    bpy.utils.unregister_class(AWG_PT_MainPanel)

if __name__ == "__main__":
    # テスト用に登録・登録解除を行う場合
    # 既に登録されている可能性を考慮して try-except で囲む
    try:
        unregister() # 既存のものをアンロード試行
    except RuntimeError: # Blenderがクラス未登録時に発生させるエラー
        pass
    except BaseException as ex: # pylint: disable=broad-except # 開発中のテスト用なので広範な例外を許可
        # BaseException を捕捉することで、SystemExit や KeyboardInterrupt も捕捉対象になるが、
        # __main__ ブロックのテストコードなので許容する。
        # 通常のコードでは Exception を使うべき。
        print(f"Unregistering AWG_PT_MainPanel failed (unexpected): {ex}")
    register()