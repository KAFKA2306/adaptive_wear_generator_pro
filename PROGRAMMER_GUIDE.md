# プログラマーガイド：Adaptive Wear Generator Pro

このドキュメントは、Blenderアドオン「Adaptive Wear Generator Pro」の内部構造と主要な機能間の連携を理解するためのプログラマー向けガイドです。

## 1. はじめに

Adaptive Wear Generator Proは、既存の素体メッシュに基づいて様々な衣装メッシュを自動生成し、素体にフィットさせるためのBlenderアドオンです。このアドオンは、以下の主要なコンポーネントで構成されています。

-   **プロパティ**: ユーザーがUIで設定する各種パラメータを保持します。
-   **オペレーター**: アドオンの主要な処理フローを制御し、各機能を連携させます。
-   **メッシュ生成**: 選択された衣装タイプに基づいた初期メッシュ形状を作成します。
-   **フィット調整**: 生成されたメッシュを素体メッシュに正確にフィットさせ、厚みを加えます。
-   **その他のユーティリティ**: UV展開、マテリアル適用、ブレンドシェイプ転送、ボーンリギング、エクスポートなどの補助機能を提供します。

## 2. 主要な機能

### 2.1. プロパティ (`core/properties.py`)

[`core/properties.py`](core/properties.py) ファイルでは、アドオンのユーザー設定を保持するためのBlenderプロパティが定義されています。主要なプロパティは [`AdaptiveWearGeneratorProPropertyGroup`](core/properties.py:21) クラス内に定義されており、オペレーターや他の機能から参照されます。

-   [`base_body`](core/properties.py:22): 衣装を生成するベースとなる素体メッシュオブジェクトへの参照を保持します。
-   [`wear_type`](core/properties.py:28): 生成する衣装のタイプ（例: パンツ、靴下、手袋など）を選択するための列挙型プロパティです。[`get_wear_types_items`](core/properties.py:11) 関数で定義されたリストから選択されます。
-   [`tight_fit`](core/properties.py:33): 生成される衣装のフィット感を素体に密着させるかどうかを制御する真偽値プロパティです。
-   [`thickness`](core/properties.py:38): 生成される衣装の厚みを設定する浮動小数点プロパティです。
-   [`sock_length`](core/properties.py:48): 衣装タイプが「靴下」の場合に、靴下の長さを設定するために使用される浮動小数点プロパティです。
-   [`glove_fingers`](core/properties.py:56): 衣装タイプが「手袋」の場合に、指あり/指なしの手袋を切り替えるために使用される真偽値プロパティです。

これらのプロパティは、通常、UIパネルを通じてユーザーによって設定され、その値がオペレーターに渡されて処理の挙動を決定します。

### 2.2. オペレーター (`core/operators.py`)

[`core/operators.py`](core/operators.py) ファイルには、アドオンの主要な実行可能なアクションであるBlenderオペレーターが定義されています。中心となるのは [`AWG_OT_GenerateWear`](core/operators.py:19) オペレーターで、衣装生成プロセス全体を orchestrate します。

[`AWG_OT_GenerateWear.execute()`](core/operators.py:25) メソッドは、以下のステップで処理を実行します。

1.  **プロパティの取得**: `context.scene.adaptive_wear_generator_pro` からユーザーが設定したプロパティ（[`base_body`](core/properties.py:22), [`wear_type`](core/properties.py:28), [`tight_fit`](core/properties.py:33), [`thickness`](core/properties.py:38) および衣装タイプ固有の追加設定）を取得します。
2.  **入力検証**: [`base_body`](core/properties.py:22) が有効なメッシュオブジェクトであるかを確認します。
3.  **メッシュ生成の呼び出し**: [`core/mesh_generator.py`](core/mesh_generator.py) に定義されている [`generate_initial_wear_mesh()`](core/mesh_generator.py:90) 関数を呼び出します。この関数には、選択された [`wear_type`](core/properties.py:28) と追加設定が渡され、基本的な衣装メッシュが生成されます。
4.  **フィット調整の呼び出し**: [`core/fit_engine.py`](core/fit_engine.py) に定義されている [`fit_wear_to_body()`](core/fit_engine.py:30) 関数を呼び出します。生成されたメッシュ、素体メッシュ、[`thickness`](core/properties.py:38)、[`tight_fit`](core/properties.py:33) の設定が渡され、メッシュが素体にフィットするように変形されます。
5.  **シーンへの追加**: フィット調整が完了したメッシュオブジェクトを現在のBlenderシーンに追加し、ユーザーが操作しやすいようにアクティブオブジェクトとして設定します。
6.  **結果報告**: 処理の成功または失敗をBlenderのインフォメーションエディターに報告します。

### 2.3. メッシュ生成 (`core/mesh_generator.py`)

[`core/mesh_generator.py`](core/mesh_generator.py) ファイルには、様々な衣装タイプの初期メッシュ形状をプログラム的に生成するための関数が含まれています。主要な関数は [`generate_initial_wear_mesh()`](core/mesh_generator.py:90) です。

[`generate_initial_wear_mesh()`](core/mesh_generator.py:90) 関数は、渡された `wear_type` に応じて内部的に異なる処理を行います。例えば、「Pants」タイプの場合は円柱と立方体を組み合わせてズボンのような形状を作成し、「Bra」タイプの場合はトーラスを変形させてブラのような形状を作成します。

また、この関数は `additional_settings` ディクショナリを受け取ります。これにより、靴下生成時の [`sock_length`](core/properties.py:48) や手袋生成時の [`glove_fingers`](core/properties.py:56) のような、特定の衣装タイプに固有の設定を生成処理に反映させることができます。

生成されるメッシュはあくまで初期形状であり、素体への正確なフィットは次のステップであるフィット調整機能に委ねられます。

### 2.4. フィット調整 (`core/fit_engine.py`)

[`core/fit_engine.py`](core/fit_engine.py) ファイルには、生成された衣装メッシュを素体メッシュにフィットさせるためのロジックが実装されています。中心となる関数は [`fit_wear_to_body()`](core/fit_engine.py:30) です。

[`fit_wear_to_body()`](core/fit_engine.py:30) 関数は、以下の主要なステップでフィット処理を行います。

1.  **シュリンクラップモディファイア**: 生成されたメッシュに「シュリンクラップ」モディファイアを追加し、ターゲットを素体メッシュに設定します。これにより、衣装メッシュの頂点が素体メッシュの表面に吸着するように変形されます。[`tight_fit`](core/properties.py:33) プロパティの値に応じて、シュリンクラップのオフセット（素体表面からの距離）が調整されます。
2.  **ソリッド化モディファイア**: シュリンクラップモディファイアの上に「ソリッド化」モディファイアを追加します。これにより、厚みのない表面メッシュに指定された [`thickness`](core/properties.py:38) に基づいた厚みが付与され、立体的な衣装メッシュが完成します。
3.  **モディファイアの適用**: 追加したシュリンクラップモディファイアとソリッド化モディファイアをメッシュデータに適用します。これにより、モディファイアによる非破壊的な変形が確定的なジオメトリ変更に変換されます。

このプロセスにより、初期形状のメッシュが素体の形状に沿って変形され、適切な厚みを持った衣装メッシュが生成されます。

## 3. 機能間の連携

Adaptive Wear Generator Proの主要な機能は、[`AWG_OT_GenerateWear`](core/operators.py:19) オペレーターを中心に有機的に連携しています。

1.  ユーザーはUIパネル（`ui/` ディレクトリ内のファイルで定義）を通じて、[`core/properties.py`](core/properties.py) で定義されたプロパティ（[`base_body`](core/properties.py:22), [`wear_type`](core/properties.py:28), [`tight_fit`](core/properties.py:33), [`thickness`](core/properties.py:38) など）を設定します。
2.  ユーザーがUIのボタンをクリックすると、[`AWG_OT_GenerateWear`](core/operators.py:19) オペレーターが実行されます。
3.  オペレーターは、まずこれらのプロパティの値を取得します。
4.  次に、[`core/mesh_generator.py`](core/mesh_generator.py) の [`generate_initial_wear_mesh()`](core/mesh_generator.py:90) 関数を呼び出し、選択された [`wear_type`](core/properties.py:28) と追加設定に基づいて初期メッシュを生成させます。
5.  生成された初期メッシュを受け取ったオペレーターは、[`core/fit_engine.py`](core/fit_engine.py) の [`fit_wear_to_body()`](core/fit_engine.py:30) 関数を呼び出し、このメッシュを素体（[`base_body`](core/properties.py:22)）にフィットさせ、[`thickness`](core/properties.py:38) と [`tight_fit`](core/properties.py:33) の設定を適用させます。
6.  フィット調整が完了した最終的なメッシュオブジェクトは、オペレーターによってBlenderシーンに追加され、ユーザーが確認・編集できるようになります。

この一連の流れを通じて、ユーザーの設定に基づいた衣装が自動的に生成され、素体にフィットした状態でシーンに配置されます。

## 4. その他のモジュール

`core/` ディレクトリには、上記の主要機能以外にも、衣装生成後の後処理や補助的な機能を提供するモジュールが含まれています。

-   [`core/uv_tools.py`](core/uv_tools.py): 生成されたメッシュのUV展開を行うための関数（例: [`unwrap_uv()`](core/uv_tools.py:1)）が含まれています。オペレーターの処理フローの中で、フィット調整後に呼び出されることがあります。
-   [`core/material_manager.py`](core/material_manager.py): 生成されたメッシュにマテリアルを適用するための関数（例: [`apply_basic_material()`](core/material_manager.py:18), [`create_lavender_material()`](core/material_manager.py:44)）が含まれています。オペレーターの処理フローの中で、メッシュ生成・フィット調整後に呼び出されることがあります。
-   [`core/blendshape_manager.py`](core/blendshape_manager.py): 素体から衣装へのブレンドシェイプ（シェイプキー）転送に関連する機能（例: [`transfer_blendshapes()`](core/blendshape_manager.py:1)）が含まれています。これは衣装生成後の追加処理として利用される可能性があります。
-   [`core/bone_rigging.py`](core/bone_rigging.py): 衣装にボーンウェイトを転送するなど、リギングに関連する機能（例: [`rig_basic_garment()`](core/bone_rigging.py:1)）が含まれています。これも衣装生成後の追加処理として利用される可能性があります。
-   [`core/export_tools.py`](core/export_tools.py): 生成された衣装を外部ファイル形式（例: FBX）としてエクスポートするための機能（例: [`export_to_fbx()`](core/export_tools.py:4)）が含まれています。
-   `services/`: ロギングサービス (`services/logging_service.py`) やVRChat関連ユーティリティ (`services/vrc_utils.py`) など、アドオン全体で利用される共通サービスが含まれています。

これらのモジュールは、主要な生成・フィット処理の後に追加の処理を実行したり、アドオンの他の部分から呼び出されたりすることで、アドオン全体の機能を提供しています。

## 5. UIとの連携

アドオンのユーザーインターフェース（UI）は、通常 `ui/` ディレクトリ内のPythonファイルで定義されます。これらのUIパネルは、[`core/properties.py`](core/properties.py) で定義されたプロパティを表示・操作するための要素（ボタン、スライダー、ドロップダウンなど）を含んでいます。

ユーザーがUIでプロパティの値を変更すると、その値はBlenderのシーンデータに格納されているアドオンのプロパティグループに反映されます。そして、ユーザーがオペレーター（例: [`AWG_OT_GenerateWear`](core/operators.py:19)）を実行すると、オペレーターはシーンデータからこれらのプロパティ値を読み取り、処理に使用します。

UIはアドオンのフロントエンドとして機能し、ユーザーとコア機能間の橋渡しをしています。

---

このガイドが、Adaptive Wear Generator Proのコードベースを理解し、開発を進める上での助けとなれば幸いです。