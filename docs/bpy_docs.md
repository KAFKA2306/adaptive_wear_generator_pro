# Blender 4.4 Python API Documentation - 日本語完全版

## 概要

Blender Python API（bpy）は、Pythonスクリプトを使用してBlenderのすべての機能にアクセスし、カスタムツールやアドオンを開発するための強力なインターフェースです。本ドキュメントは、AdaptiveWear Generator Proプロジェクトに基づく実践的なAPI使用方法を詳細に解説します。

## 基本モジュール構成

### **bpy（Blender Python）**
Blenderの主要Python APIモジュール

```python
import bpy

# よく使用される基本アクセサ
bpy.context    # 現在のコンテキスト情報
bpy.data       # Blenderデータブロックへのアクセス
bpy.ops        # Blenderオペレーターの実行
bpy.types      # Blenderの型定義
bpy.props      # プロパティ定義用モジュール
```

### **bmesh**
メッシュデータの高速編集用モジュール

```python
import bmesh

# 基本的な使用パターン
bm = bmesh.new()                    # 新しいbmeshインスタンス作成
bm.from_mesh(mesh_data)             # 既存メッシュからデータ読み込み
bm.to_mesh(mesh_data)               # bmeshデータをメッシュに書き戻し
bm.free()                           # メモリ解放
```

## アドオン開発基礎

### **アドオン初期化構造**

```python
bl_info = {
    "name": "アドオン名",
    "author": "作成者名",
    "version": (0, 1, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > タブ名",
    "description": "アドオンの説明",
    "category": "Object",
}

import bpy
from bpy.props import PointerProperty

# クラス登録リスト
classes = (
    プロパティクラス,
    オペレータークラス,
    パネルクラス,
)

def register():
    """アドオン登録処理"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # プロパティをシーンに追加
    bpy.types.Scene.custom_properties = PointerProperty(
        type=プロパティクラス
    )

def unregister():
    """アドオン登録解除処理"""
    # プロパティ削除
    if hasattr(bpy.types.Scene, 'custom_properties'):
        del bpy.types.Scene.custom_properties
    
    # クラス登録解除
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
```

## プロパティシステム

### **プロパティ定義**

```python
from bpy.props import (
    PointerProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    StringProperty,
)
from bpy.types import PropertyGroup, Object

class CustomPropertyGroup(PropertyGroup):
    """カスタムプロパティグループ"""
    
    # オブジェクト選択用ポインタープロパティ
    target_object: PointerProperty(
        name="対象オブジェクト",
        description="処理対象となるオブジェクト",
        type=Object,
        poll=lambda self, obj: obj.type == 'MESH',  # メッシュのみ選択可能
    )
    
    # 列挙型プロパティ
    operation_type: EnumProperty(
        name="操作タイプ",
        description="実行する操作を選択",
        items=[
            ("TYPE_A", "タイプA", "タイプAの処理を実行"),
            ("TYPE_B", "タイプB", "タイプBの処理を実行"),
        ],
        default="TYPE_A",
    )
    
    # ブール型プロパティ
    enable_feature: BoolProperty(
        name="機能を有効化",
        description="特定機能の有効/無効を切り替え",
        default=False,
    )
    
    # 浮動小数点プロパティ
    thickness_value: FloatProperty(
        name="厚み",
        description="厚みの値を設定",
        default=0.01,
        min=0.0,
        soft_max=0.1,
        step=0.1,
        precision=3,
        unit='LENGTH',
    )
```

### **プロパティアクセス**

```python
def get_properties(context):
    """シーンからプロパティを取得"""
    scene = context.scene
    props = scene.custom_properties
    
    target_obj = props.target_object
    op_type = props.operation_type
    is_enabled = props.enable_feature
    thickness = props.thickness_value
    
    return target_obj, op_type, is_enabled, thickness
```

## オペレーター開発

### **基本オペレーター構造**

```python
from bpy.types import Operator

class CUSTOM_OT_ProcessMesh(Operator):
    """カスタムメッシュ処理オペレーター"""
    bl_idname = "custom.process_mesh"
    bl_label = "メッシュ処理"
    bl_description = "選択されたメッシュに対して処理を実行"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """オペレーター実行処理"""
        try:
            # プロパティ取得
            props = context.scene.custom_properties
            
            # 入力検証
            if not self.validate_input(props):
                return {'CANCELLED'}
            
            # メイン処理
            result = self.process_mesh(props)
            
            if result:
                self.report({'INFO'}, "処理が完了しました")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "処理に失敗しました")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"エラーが発生しました: {str(e)}")
            return {'CANCELLED'}

    def validate_input(self, props):
        """入力値検証"""
        if props.target_object is None:
            self.report({'ERROR'}, "対象オブジェクトが選択されていません")
            return False
        
        if props.target_object.type != 'MESH':
            self.report({'ERROR'}, "メッシュオブジェクトを選択してください")
            return False
        
        return True

    def process_mesh(self, props):
        """実際のメッシュ処理"""
        # 具体的な処理を実装
        return True
```

## メッシュ操作

### **bmeshを使用したメッシュ編集**

```python
import bmesh

def create_custom_mesh(base_obj, settings):
    """カスタムメッシュの生成"""
    
    # 基本オブジェクトを複製
    duplicate_obj = duplicate_object(base_obj, "_custom")
    
    # 編集モードに切り替え
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    # bmeshインスタンス作成
    bm = bmesh.from_edit_mesh(duplicate_obj.data)
    
    try:
        # 頂点グループベースの選択
        vertex_group = find_vertex_group(duplicate_obj, ['target_group'])
        if vertex_group:
            select_vertices_by_group(bm, duplicate_obj, vertex_group, 0.5)
        
        # 選択されていない頂点を削除
        selected_verts = [v for v in bm.verts if v.select]
        remove_verts = [v for v in bm.verts if v not in selected_verts]
        bmesh.ops.delete(bm, geom=remove_verts, context='VERTS')
        
        # 厚みを追加
        if settings.thickness > 0:
            bmesh.ops.solidify(bm, geom=bm.faces, thickness=settings.thickness)
        
        # メッシュを更新
        bmesh.update_edit_mesh(duplicate_obj.data)
        
    finally:
        bm.free()
        bpy.ops.object.mode_set(mode='OBJECT')
    
    return duplicate_obj

def duplicate_object(base_obj, suffix):
    """オブジェクトの複製"""
    # 現在の選択状態を保存
    original_active = bpy.context.view_layer.objects.active
    original_selected = bpy.context.selected_objects[:]
    
    try:
        # 対象オブジェクトを選択
        bpy.ops.object.select_all(action='DESELECT')
        base_obj.select_set(True)
        bpy.context.view_layer.objects.active = base_obj
        
        # 複製実行
        bpy.ops.object.duplicate()
        new_obj = bpy.context.active_object
        new_obj.name = base_obj.name + suffix
        
        return new_obj
        
    finally:
        # 選択状態復元
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selected:
            if obj.name in bpy.data.objects:
                obj.select_set(True)
        if original_active and original_active.name in bpy.data.objects:
            bpy.context.view_layer.objects.active = original_active

def find_vertex_group(obj, group_names):
    """頂点グループの検索"""
    for group_name in group_names:
        for vg in obj.vertex_groups:
            if group_name.lower() in vg.name.lower():
                return vg
    return None

def select_vertices_by_group(bm, obj, vertex_group, min_weight):
    """頂点グループに基づく頂点選択"""
    deform_layer = bm.verts.layers.deform.verify()
    
    for vert in bm.verts:
        if vertex_group.index in vert[deform_layer]:
            weight = vert[deform_layer][vertex_group.index]
            vert.select = weight >= min_weight
        else:
            vert.select = False
```

### **メッシュデータの直接作成**

```python
def create_mesh_from_data(name, vertices, faces):
    """頂点と面データからメッシュを作成"""
    
    # メッシュデータ作成
    mesh_data = bpy.data.meshes.new(name)
    mesh_data.from_pydata(vertices, [], faces)
    mesh_data.update()
    
    # オブジェクト作成
    mesh_obj = bpy.data.objects.new(name, mesh_data)
    
    # シーンに追加
    bpy.context.collection.objects.link(mesh_obj)
    
    return mesh_obj

# 使用例：立方体の作成
vertices = [
    (-1.0, -1.0, -1.0), (1.0, -1.0, -1.0), 
    (1.0, 1.0, -1.0), (-1.0, 1.0, -1.0),
    (-1.0, -1.0, 1.0), (1.0, -1.0, 1.0), 
    (1.0, 1.0, 1.0), (-1.0, 1.0, 1.0)
]

faces = [
    (0, 1, 2, 3), (4, 7, 6, 5),
    (0, 4, 5, 1), (1, 5, 6, 2), 
    (2, 6, 7, 3), (4, 0, 3, 7)
]

cube_obj = create_mesh_from_data("CustomCube", vertices, faces)
```

## モディファイア操作

### **Shrinkwrapモディファイア（フィッティング）**

```python
def apply_shrinkwrap_fitting(target_obj, source_obj, settings):
    """Shrinkwrapモディファイアを使用したフィッティング"""
    
    # 既存のShrinkwrapモディファイアを削除
    for modifier in target_obj.modifiers:
        if modifier.type == 'SHRINKWRAP':
            target_obj.modifiers.remove(modifier)
    
    # 新しいShrinkwrapモディファイアを追加
    shrinkwrap_mod = target_obj.modifiers.new(name="Shrinkwrap", type='SHRINKWRAP')
    shrinkwrap_mod.target = source_obj
    
    # 設定適用
    if settings.tight_fit:
        shrinkwrap_mod.wrap_method = 'PROJECT'
        shrinkwrap_mod.use_project_x = True
        shrinkwrap_mod.use_project_y = True
        shrinkwrap_mod.use_project_z = True
        shrinkwrap_mod.offset = 0.001
    else:
        shrinkwrap_mod.wrap_method = 'NEAREST_SURFACEPOINT'
        shrinkwrap_mod.offset = settings.thickness * 0.5
    
    # モディファイア適用
    bpy.context.view_layer.objects.active = target_obj
    bpy.ops.object.modifier_apply(modifier=shrinkwrap_mod.name)
```

### **Solidifyモディファイア（厚み追加）**

```python
def add_thickness_modifier(obj, thickness):
    """Solidifyモディファイアで厚みを追加"""
    
    if thickness = 1.0 else 'BLEND'
    
    # ノードツリークリア
    mat.node_tree.nodes.clear()
    
    # Principled BSDFノード追加
    principled = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    
    # Material Outputノード追加
    output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # ノード接続
    mat.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # プロパティ設定
    principled.inputs['Base Color'].default_value = base_color
    principled.inputs['Alpha'].default_value = alpha
    principled.inputs['Roughness'].default_value = roughness
    
    # Blender 4.x対応：Specular設定
    if "Specular IOR Level" in principled.inputs:
        principled.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in principled.inputs:
        principled.inputs["Specular"].default_value = specular
    
    return mat

def apply_material_to_object(obj, material):
    """オブジェクトにマテリアルを適用"""
    
    # マテリアルスロットをクリア
    obj.data.materials.clear()
    
    # マテリアルを追加
    obj.data.materials.append(material)
    
    return True
```

### **マテリアルプリセット管理**

```python
import json
import os

def load_material_presets(preset_file_path):
    """マテリアルプリセットの読み込み"""
    
    try:
        with open(preset_file_path, 'r', encoding='utf-8') as f:
            presets = json.load(f)
        return presets
        
    except FileNotFoundError:
        print(f"プリセットファイルが見つかりません: {preset_file_path}")
        return []
    except json.JSONDecodeError:
        print(f"プリセットファイルの形式が不正です: {preset_file_path}")
        return []
    except Exception as e:
        print(f"プリセット読み込みエラー: {str(e)}")
        return []

def create_material_from_preset(preset_data):
    """プリセットデータからマテリアル作成"""
    
    name = preset_data.get("name", "DefaultMaterial")
    color = tuple(preset_data.get("color", [0.8, 0.8, 0.8, 1.0]))
    alpha = preset_data.get("alpha", 1.0)
    specular = preset_data.get("specular", 0.5)
    roughness = preset_data.get("roughness", 0.5)
    
    return create_principled_material(
        name=name,
        base_color=color,
        alpha=alpha,
        specular=specular,
        roughness=roughness
    )

# プリセットファイル例（JSON）
"""
[
  {
    "name": "Cotton_Material",
    "color": [0.9, 0.9, 0.9, 1.0],
    "alpha": 1.0,
    "specular": 0.2,
    "roughness": 0.9
  },
  {
    "name": "Silk_Material",
    "color": [0.9, 0.7, 0.8, 1.0],
    "alpha": 1.0,
    "specular": 0.6,
    "roughness": 0.3
  }
]
"""
```

## UIパネル開発

### **基本パネル構造**

```python
from bpy.types import Panel

class CUSTOM_PT_MainPanel(Panel):
    """メインパネルクラス"""
    bl_label = "カスタムツール"
    bl_idname = "CUSTOM_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "カスタムタブ"

    def draw(self, context):
        """パネル描画処理"""
        layout = self.layout
        scene = context.scene
        props = scene.custom_properties
        
        # 基本設定セクション
        self.draw_basic_settings(layout, props)
        
        # 詳細設定セクション
        self.draw_advanced_settings(layout, props)
        
        # 実行ボタン
        self.draw_action_buttons(layout, props)

    def draw_basic_settings(self, layout, props):
        """基本設定の描画"""
        box = layout.box()
        box.label(text="基本設定", icon='OBJECT_DATA')
        
        row = box.row()
        row.prop(props, "target_object")
        
        row = box.row()
        row.prop(props, "operation_type")

    def draw_advanced_settings(self, layout, props):
        """詳細設定の描画"""
        box = layout.box()
        box.label(text="詳細設定", icon='SETTINGS')
        
        row = box.row()
        row.prop(props, "enable_feature")
        
        row = box.row()
        row.prop(props, "thickness_value")

    def draw_action_buttons(self, layout, props):
        """アクションボタンの描画"""
        layout.separator()
        
        row = layout.row(align=True)
        row.scale_y = 1.5
        
        # ボタンの有効/無効制御
        is_valid = self.validate_settings(props)
        row.enabled = is_valid
        
        row.operator("custom.process_mesh", text="処理実行", icon='PLAY')
        
        # 検証エラー表示
        if not is_valid:
            layout.label(text="設定を確認してください", icon='ERROR')

    def validate_settings(self, props):
        """設定の検証"""
        if props.target_object is None:
            return False
        if props.target_object.type != 'MESH':
            return False
        return True
```

### **動的UI要素**

```python
def draw_conditional_ui(self, layout, props):
    """条件に応じた動的UI表示"""
    
    # 操作タイプに応じて異なるオプションを表示
    if props.operation_type == "TYPE_A":
        box = layout.box()
        box.label(text="タイプA設定", icon='MODIFIER')
        box.prop(props, "type_a_specific_option")
        
    elif props.operation_type == "TYPE_B":
        box = layout.box()
        box.label(text="タイプB設定", icon='MODIFIER')
        box.prop(props, "type_b_specific_option")
    
    # 機能が有効な場合のみ追加オプションを表示
    if props.enable_feature:
        box = layout.box()
        box.label(text="追加オプション", icon='PLUS')
        box.prop(props, "additional_option")

def draw_progress_indicator(self, layout, progress_value):
    """進行状況表示"""
    box = layout.box()
    box.label(text=f"進行状況: {progress_value:.1%}")
    
    # プログレスバー的な表示
    row = box.row()
    sub = row.row()
    sub.scale_x = progress_value
    sub.label(text="█" * int(progress_value * 20))
```

## エラーハンドリングとデバッグ

### **ロギングシステム**

```python
import logging
from datetime import datetime

class BlenderLogger:
    """Blender専用ロガークラス"""
    
    def __init__(self, name="CustomAddon"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # ハンドラー設定
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message):
        """情報ログ"""
        self.logger.info(message)
    
    def warning(self, message):
        """警告ログ"""
        self.logger.warning(message)
    
    def error(self, message):
        """エラーログ"""
        self.logger.error(message)
    
    def debug(self, message):
        """デバッグログ"""
        self.logger.debug(message)

# グローバルロガーインスタンス
logger = BlenderLogger()
```

### **例外処理パターン**

```python
def safe_execute_operation(operation_func, *args, **kwargs):
    """安全な操作実行ラッパー"""
    
    try:
        result = operation_func(*args, **kwargs)
        logger.info(f"操作 '{operation_func.__name__}' が正常に完了しました")
        return result, True
        
    except Exception as e:
        error_msg = f"操作 '{operation_func.__name__}' でエラーが発生: {str(e)}"
        logger.error(error_msg)
        return None, False

def validate_blender_context():
    """Blenderコンテキストの検証"""
    
    if not hasattr(bpy, 'context'):
        raise RuntimeError("Blenderコンテキストが利用できません")
    
    if not bpy.context.scene:
        raise RuntimeError("アクティブなシーンがありません")
    
    return True

def cleanup_on_error(created_objects):
    """エラー時のクリーンアップ"""
    
    for obj in created_objects:
        if obj and obj.name in bpy.data.objects:
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
                logger.info(f"エラー時クリーンアップ: {obj.name} を削除しました")
            except Exception as e:
                logger.warning(f"オブジェクト削除に失敗: {str(e)}")
```

## パフォーマンス最適化

### **大量データ処理の最適化**

```python
def batch_process_objects(objects, process_func, batch_size=100):
    """バッチ処理による最適化"""
    
    total_objects = len(objects)
    processed = 0
    
    for i in range(0, total_objects, batch_size):
        batch = objects[i:i + batch_size]
        
        # バッチ処理実行
        for obj in batch:
            process_func(obj)
            processed += 1
        
        # 進行状況報告
        progress = processed / total_objects
        logger.info(f"バッチ処理進行状況: {progress:.1%} ({processed}/{total_objects})")
        
        # メモリクリーンアップ
        if i % (batch_size * 10) == 0:
            import gc
            gc.collect()

def optimize_viewport_for_processing():
    """処理時のビューポート最適化"""
    
    # ビューポートオーバーレイを無効化
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.overlay.show_overlays = False
                    space.shading.type = 'SOLID'
                    break

def restore_viewport_settings():
    """ビューポート設定の復元"""
    
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.overlay.show_overlays = True
                    break
```

## 実践的な使用例

### **完全なワークフロー例**

```python
def complete_garment_generation_workflow():
    """完全な衣装生成ワークフロー"""
    
    logger.info("衣装生成ワークフローを開始します")
    created_objects = []
    
    try:
        # 1. 入力検証
        validate_blender_context()
        props = bpy.context.scene.custom_properties
        
        if not validate_input_properties(props):
            raise ValueError("入力プロパティが不正です")
        
        # 2. ビューポート最適化
        optimize_viewport_for_processing()
        
        # 3. メッシュ生成
        logger.info("メッシュ生成を開始します")
        garment_mesh, success = safe_execute_operation(
            create_custom_mesh, 
            props.target_object, 
            props
        )
        
        if not success or not garment_mesh:
            raise RuntimeError("メッシュ生成に失敗しました")
        
        created_objects.append(garment_mesh)
        
        # 4. フィッティング適用
        logger.info("フィッティング処理を開始します")
        fitting_success = safe_execute_operation(
            apply_shrinkwrap_fitting,
            garment_mesh,
            props.target_object,
            props
        )[1]
        
        if not fitting_success:
            raise RuntimeError("フィッティング処理に失敗しました")
        
        # 5. リギング適用
        armature = get_armature_from_object(props.target_object)
        if armature:
            logger.info("リギング処理を開始します")
            
            rigging_success = safe_execute_operation(
                setup_armature_modifier,
                garment_mesh,
                armature
            )[1]
            
            if rigging_success:
                weight_transfer_success = safe_execute_operation(
                    transfer_vertex_weights,
                    props.target_object,
                    garment_mesh
                )[1]
                
                if not weight_transfer_success:
                    logger.warning("ウェイト転送に失敗しましたが、処理を続行します")
        
        # 6. マテリアル適用
        logger.info("マテリアル適用を開始します")
        material = create_principled_material(
            name=f"{props.operation_type}_Material",
            base_color=(0.8, 0.2, 0.2, 1.0)
        )
        
        material_success = safe_execute_operation(
            apply_material_to_object,
            garment_mesh,
            material
        )[1]
        
        if not material_success:
            logger.warning("マテリアル適用に失敗しましたが、処理を続行します")
        
        # 7. 最終選択設定
        bpy.ops.object.select_all(action='DESELECT')
        garment_mesh.select_set(True)
        bpy.context.view_layer.objects.active = garment_mesh
        
        logger.info("衣装生成ワークフローが正常に完了しました")
        return garment_mesh
        
    except Exception as e:
        logger.error(f"ワークフロー実行中にエラーが発生しました: {str(e)}")
        cleanup_on_error(created_objects)
        raise
        
    finally:
        # ビューポート設定復元
        restore_viewport_settings()

def validate_input_properties(props):
    """入力プロパティの検証"""
    
    if not props.target_object:
        logger.error("対象オブジェクトが選択されていません")
        return False
    
    if props.target_object.type != 'MESH':
        logger.error("選択されたオブジェクトがメッシュではありません")
        return False
    
    if props.operation_type == "NONE":
        logger.error("操作タイプが選択されていません")
        return False
    
    return True
```

このドキュメンテーションは、Blender 4.4 Python APIの実践的な使用方法を網羅的に解説しており、AdaptiveWear Generator Proプロジェクトで実際に使用されているパターンに基づいています。各セクションは独立して参照でき、具体的なコード例とともに詳細な説明を提供しています。