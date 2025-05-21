# ミニマル下着生成アドオン - MVP構築計画

## MVPの定義

指定された素体メッシュから「hip」または「腰」の頂点グループに基づいてパンツメッシュを生成し、半透明のラベンダーマテリアルを適用する機能。

## ステップバイステップ計画

この計画は、既存のコードを整理し、アドオンとして機能させるための最小限のステップを定義します。各ステップは独立して実行・テスト可能です。

1.  **アドオンエントリーポイントの準備**
    *   **目的**: アドオンの基本情報を定義し、Blenderに認識・登録されるための最小限の枠組みを作成する。
    *   **対象ファイル**: [`__init__.py`](__init__.py)
    *   **内容**:
        -   `bl_info` ディクショナリを追加し、アドオン名、バージョン、作者などの基本情報を設定する。
        -   `register()` 関数と `unregister()` 関数を定義する。現時点では、これらの関数の中身は空（`pass` ステートメントのみ）とする。
    *   **完了条件**:
        -   [`__init__.py`](__init__.py) ファイルが存在し、`bl_info` ディクショナリ、空の `register()` 関数、空の `unregister()` 関数が含まれていること。
        -   Blenderの「Preferences」->「Add-ons」リストにアドオン名が表示されることを確認する（有効化はまだできません）。

2.  **プロパティグループの定義**
    *   **目的**: 素体オブジェクトへの参照を保持するためのカスタムプロパティグループクラスを定義する。
    *   **対象ファイル**: [`core/properties.py`](core/properties.py)
    *   **内容**:
        -   `bpy.types.PropertyGroup` を継承した `UnderwearProps` クラスを定義する。
        -   このクラス内に、素体オブジェクトをリンクするための `bpy.props.PointerProperty` (`base_body`) を追加する。`type` を `bpy.types.Object` に設定する。
    *   **完了条件**:
        -   [`core/properties.py`](core/properties.py) ファイルが作成され、`UnderwearProps` クラスが正しく定義されていること。

3.  **UIパネルの定義**
    *   **目的**: アドオンのUIを表示するためのパネルクラスを定義する。
    *   **対象ファイル**: [`ui/panel_main.py`](ui/panel_main.py)
    *   **内容**:
        -   `bpy.types.Panel` を継承した `UNDERWEAR_PT_Main` クラスを定義する。
        -   `bl_label`, `bl_space_type`, `bl_region_type`, `bl_category` などのパネル属性を設定する。
        -   `draw(self, context)` メソッドを定義する。現時点では、このメソッドの中身は空（`pass` ステートメントのみ）とするか、簡単なテキストラベルを表示するだけにする。
    *   **完了条件**:
        -   [`ui/panel_main.py`](ui/panel_main.py) ファイルが作成され、`UNDERWEER_PT_Main` クラスが正しく定義されていること。

4.  **メッシュ生成ロジックの配置**
    *   **目的**: パンツメッシュを生成するコアロジック関数を適切なファイルに配置する。
    *   **対象ファイル**: [`core/mesh_generator.py`](core/mesh_generator.py)
    *   **内容**:
        -   提供されたコードから `create_pants_mesh(base_obj)` 関数を抽出し、[`core/mesh_generator.py`](core/mesh_generator.py) ファイルに移動または記述する。
        -   関数が必要とする `bpy` や `bmesh` モジュールをインポートする。
    *   **完了条件**:
        -   [`core/mesh_generator.py`](core/mesh_generator.py) ファイルが存在し、`create_pants_mesh` 関数が正しく定義されていること。

5.  **マテリアル生成ロジックの配置**
    *   **目的**: ラベンダー色の半透明マテリアルを作成するコアロジック関数を適切なファイルに配置する。
    *   **対象ファイル**: [`core/material_manager.py`](core/material_manager.py)
    *   **内容**:
        -   提供されたコードから `create_lavender_material()` 関数を抽出し、[`core/material_manager.py`](core/material_manager.py) ファイルに移動または記述する。
        -   関数が必要とする `bpy` モジュールをインポートする。
    *   **完了条件**:
        -   [`core/material_manager.py`](core/material_manager.py) ファイルが作成され、`create_lavender_material` 関数が正しく定義されていること。

6.  **オペレーターの定義**
    *   **目的**: UIからのアクション（パンツ生成）を実行するためのオペレータークラスを定義する。
    *   **対象ファイル**: [`core/operators.py`](core/operators.py)
    *   **内容**:
        -   `bpy.types.Operator` を継承した `UNDERWEAR_OT_Generate` クラスを定義する。
        -   `bl_idname` と `bl_label` を設定する。
        -   `execute(self, context)` メソッドを定義する。現時点では、このメソッドは簡単なレポートメッセージ（例: `self.report({'INFO'}, "Generate operator called")`）を表示するだけのスタブとする。
    *   **完了条件**:
        -   [`core/operators.py`](core/operators.py) ファイルが作成され、`UNDERWEAR_OT_Generate` クラスが正しく定義されていること。

7.  **`__init__.py` でのクラス登録とプロパティリンク**
    *   **目的**: ステップ2, 3, 6で定義したクラスをBlenderに登録し、シーンプロパティにリンクする。
    *   **対象ファイル**: [`__init__.py`](__init__.py)
    *   **内容**:
        -   [`core/properties.py`](core/properties.py) から `UnderwearProps` をインポートする。
        -   [`ui/panel_main.py`](ui/panel_main.py) から `UNDERWEAR_PT_Main` をインポートする。
        -   [`core/operators.py`](core/operators.py) から `UNDERWEAR_OT_Generate` をインポートする。
        -   登録するクラスのリスト `classes` を定義する。
        -   `register()` 関数内で、`classes` リストの各クラスを `bpy.utils.register_class()` で登録する。
        -   `register()` 関数内で、`bpy.types.Scene.underwear_props = bpy.props.PointerProperty(type=UnderwearProps)` を使用して、シーンデータに `UnderwearProps` をリンクする。
        -   `unregister()` 関数内で、登録時と逆の順序で `bpy.utils.unregister_class()` を使用して登録解除する。
        -   `unregister()` 関数内で、`del bpy.types.Scene.underwear_props` を使用してシーンプロパティのリンクを解除する。
    *   **完了条件**:
        -   [`__init__.py`](__init__.py) が正しく編集され、Blenderでアドオンを有効化できるようになること。
        -   アドオンを有効化/無効化してもBlenderがエラーを出力しないことを確認する。

8.  **UIパネルへのプロパティとオペレーターの紐付け**
    *   **目的**: UIパネルに素体選択フィールドと生成ボタンを表示し、それらを定義したプロパティとオペレーターにリンクする。
    *   **対象ファイル**: [`ui/panel_main.py`](ui/panel_main.py)
    *   **内容**:
        -   `UNDERWEAR_PT_Main` クラスの `draw(self, context)` メソッドを編集する。
        -   `context.scene.underwear_props` を取得する。
        -   `layout.prop_search()` を使用して、素体選択用のUI要素を追加し、`context.scene.underwear_props.base_body` にリンクする。検索対象は `bpy.data.objects` とする。
        -   `layout.operator()` を使用して、パンツ生成ボタンを追加し、ステップ6で定義したオペレーターの `bl_idname` ("underwear.generate") にリンクする。
    *   **完了条件**:
        -   Blenderの3DビューポートのUI領域にアドオンのパネルが表示されること。
        -   パネル内に「素体」というラベルのオブジェクト選択フィールドと、「パンツ生成」というラベルのボタンが表示されること。
        -   ボタンをクリックした際に、ステップ6で実装したオペレーターのスタブが実行されることを確認する（レポートメッセージが表示されるなど）。

9.  **オペレーターからのコアロジック呼び出し**
    *   **目的**: オペレーターが、メッシュ生成とマテリアル適用を行うコアロジック関数を呼び出すように実装する。
    *   **対象ファイル**: [`core/operators.py`](core/operators.py)
    *   **内容**:
        -   [`core/mesh_generator.py`](core/mesh_generator.py) から `create_pants_mesh` 関数をインポートする。
        -   [`core/material_manager.py`](core/material_manager.py) から `create_lavender_material` 関数をインポートする。
        -   `UNDERWEAR_OT_Generate` クラスの `execute(self, context)` メソッドを編集する。
        -   `context.scene.underwear_props.base_body` から素体オブジェクトを取得する。
        -   素体オブジェクトが有効なメッシュオブジェクトであるかチェックし、無効な場合はエラーをレポートして処理を終了する。
        -   `create_pants_mesh` 関数を呼び出し、生成されたパンツオブジェクトを取得する。
        -   パンツオブジェクトが正常に生成されたかチェックし、失敗した場合はエラーをレポートして処理を終了する。
        -   `create_lavender_material` 関数を呼び出し、マテリアルを取得する。
        -   生成されたパンツオブジェクトのデータにマテリアルを適用する。
        -   成功メッセージをレポートする。
    *   **完了条件**:
        -   Blender上で有効な素体を選択し、パネルのボタンをクリックすると、新しいパンツメッシュオブジェクトが生成され、ラベンダー色の半透明マテリアルが適用されること。
        -   素体が選択されていない場合や、選択されたオブジェクトがメッシュでない場合に、適切なエラーメッセージがBlenderのインフォエディタに表示されること。
        -   素体に「hip」または「腰」の頂点グループが存在しない場合に、適切なエラーメッセージが表示されること。

10. **基本的な動作確認テスト**
    *   **目的**: MVPとして定義された主要機能が、実際のBlender環境で意図通りに動作することを確認する。
    *   **内容**:
        -   Blenderを起動し、アドオンを有効化する。
        -   テスト用のメッシュオブジェクト（例: 人型モデル）を用意し、「hip」または「腰」という名前の頂点グループを作成し、腰周りの頂点にウェイトを設定する。
        -   アドオンパネルでそのメッシュオブジェクトを素体として選択する。
        -   「パンツ生成」ボタンをクリックする。
        -   新しいメッシュオブジェクトが生成され、元の素体の腰周りの形状を反映していること、およびラベンダー色の半透明マテリアルが適用されていることを目視で確認する。
        -   素体を選択しない、メッシュ以外のオブジェクトを選択する、頂点グループがない、といったエラーケースも試行し、適切なエラーメッセージが表示されることを確認する。
    *   **完了条件**:
        -   上記の内容が全て確認でき、MVPとして定義された機能が期待通りに動作すること。