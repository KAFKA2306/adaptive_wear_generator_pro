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

## 3. 動作原理とソフトウェアワークフロー

このセクションでは、Adaptive Wear Generator Proが内部でどのように動作し、ユーザーの操作から結果が生成されるまでの一連のワークフローを詳細に解説します。

### 3.1. 動作原理

#### 3.1.1. プロパティとUIの連携

[`core/properties.py`](core/properties.py) で定義されたプロパティは、Blenderのシーンデータに格納されるカスタムプロパティグループ（[`AdaptiveWearGeneratorProPropertyGroup`](core/properties.py:21)）として登録されます。UIパネル（`ui/` ディレクトリ内のファイルで定義）は、これらのプロパティを操作するためのGUI要素（ボタン、スライダー、ドロップダウンメニューなど）を提供します。

ユーザーがUIで値を変更すると、その変更はリアルタイムでシーンデータのプロパティグループに反映されます。オペレーターが実行される際には、このプロパティグループから現在の設定値が読み込まれます。これにより、UIでのユーザー入力がアドオンのコア機能に連携されます。

#### 3.1.2. メッシュ生成の仕組み (`core/mesh_generator.py`)

[`core/mesh_generator.py`](core/mesh_generator.py) の [`generate_initial_wear_mesh()`](core/mesh_generator.py:90) 関数は、選択された [`wear_type`](core/properties.py:28) に基づいて、BlenderのPython API (`bpy.ops.mesh.primitive_*_add`) を使用して基本的なプリミティブ（円柱、球、トーラス、立方体など）を組み合わせて初期メッシュ形状を作成します。

-   **衣装タイプごとの分岐**: 関数内部では、`if/elif` 構造を使用して `wear_type` の値に応じた処理に分岐します。
-   **プリミティブの組み合わせ**: 各衣装タイプに対応するセクションでは、必要な数のプリミティブが特定のサイズ、位置、回転、スケールで作成されます。例えば、パンツは2つの円柱（脚）と1つの立方体（股）を組み合わせて作成されます。
-   **追加設定の適用**: `additional_settings` ディクショナリを通じて渡される [`sock_length`](core/properties.py:48) や [`glove_fingers`](core/properties.py:56) のようなパラメータは、プリミティブのサイズや形状、あるいは生成するプリミティブの種類（例: 指あり/指なし手袋）を決定するために使用されます。
-   **オブジェクトの結合**: 複数のプリミティブで構成される衣装の場合、`bpy.ops.object.join()` オペレーターを使用してそれらを1つのメッシュオブジェクトに結合します。
-   **トランスフォームの適用**: 生成されたメッシュオブジェクトの位置、回転、スケールがリセットされ、これらのトランスフォームがメッシュデータ自体に適用されます (`bpy.ops.object.transform_apply`)。これにより、後続のフィット調整処理などが正確に行われるようになります。

この段階で生成されるメッシュは、あくまで素体の形状にフィットさせるための「土台」となる基本的な形状です。

#### 3.1.3. フィット調整の仕組み (`core/fit_engine.py`)

[`core/fit_engine.py`](core/fit_engine.py) の [`fit_wear_to_body()`](core/fit_engine.py:30) 関数は、Blenderのモディファイアシステムを活用してメッシュのフィット調整と厚み付けを行います。

-   **シュリンクラップモディファイア**: 生成された衣装メッシュに「シュリンクラップ」モディファイアを追加します。このモディファイアの `target` プロパティには素体メッシュオブジェクトが設定されます。`wrap_method` は通常 'PROJECT' または 'NEAREST_SURFACEPOINT' が使用され、衣装メッシュの頂点を素体メッシュの表面に投影または吸着させます。`offset` プロパティは、衣装メッシュが素体表面からどれだけ離れるかを制御します。[`tight_fit`](core/properties.py:33) プロパティがTrueの場合、このオフセットは小さく設定され、より密着したフィット感を実現します。
-   **ソリッド化モディファイア**: シュリンクラップモディファイアの上に「ソリッド化」モディファイアを追加します。このモディファイアの `thickness` プロパティには、ユーザーが設定した [`thickness`](core/properties.py:38) の値が適用されます。これにより、シュリンクラップによって素体表面に沿う形に変形されたメッシュに、指定された厚みが付与され、立体的な形状になります。`offset` プロパティは厚みを内側または外側のどちらに付けるかを制御し、通常は外側 (`offset = 1`) に設定されます。
-   **モディファイアの適用**: `bpy.ops.object.modifier_apply()` オペレーターを使用して、追加したシュリンクラップモディファイアとソリッド化モディファイアを順番にメッシュデータに適用します。これにより、モディファイアによる非破壊的な変形が確定的なジオメトリ変更となり、最終的な衣装メッシュが完成します。

このモディファイアベースのアプローチにより、効率的かつ柔軟なメッシュのフィット調整と厚み付けを実現しています。

### 3.2. ソフトウェアワークフロー

Adaptive Wear Generator Proのソフトウェアワークフローは、ユーザーの操作を起点として、以下のステップで進行します。

1.  **UIでの設定**: ユーザーはBlenderの3DビューポートサイドバーにあるアドオンのUIパネルを通じて、生成したい衣装のタイプ、素体オブジェクト、フィット感、厚みなどのパラメータを [`core/properties.py`](core/properties.py) で定義されたプロパティに設定します。これらの設定値はBlenderのシーンデータに一時的に保存されます。
2.  **オペレーターの実行**: ユーザーがUIパネル上の「Generate Wear」ボタン（または対応するボタン）をクリックすると、[`AWG_OT_GenerateWear`](core/operators.py:19) オペレーターが実行されます。
3.  **プロパティの読み込み**: オペレーターの [`execute()`](core/operators.py:25) メソッドが開始され、まず `context.scene.adaptive_wear_generator_pro` から現在のプロパティ設定値（[`base_body`](core/properties.py:22), [`wear_type`](core/properties.py:28), [`tight_fit`](core/properties.py:33), [`thickness`](core/properties.py:38), 追加設定など）を読み込みます。
4.  **入力検証**: 読み込んだプロパティのうち、必須である [`base_body`](core/properties.py:22) が有効なメッシュオブジェクトであるかを確認します。無効な場合はエラーを報告し、処理を中断します。
5.  **初期メッシュ生成**: [`core/mesh_generator.py`](core/mesh_generator.py) の [`generate_initial_wear_mesh()`](core/mesh_generator.py:90) 関数が呼び出されます。オペレーターから渡された [`wear_type`](core/properties.py:28) と追加設定に基づいて、基本的な形状のメッシュオブジェクトがBlenderシーンに一時的に作成されます。
6.  **フィット調整**: [`core/fit_engine.py`](core/fit_engine.py) の [`fit_wear_to_body()`](core/fit_engine.py:30) 関数が呼び出されます。生成された初期メッシュ、素体メッシュ、[`thickness`](core/properties.py:38)、[`tight_fit`](core/properties.py:33) の設定が渡され、メッシュにシュリンクラップモディファイアとソリッド化モディファイアが適用・確定され、素体にフィットした厚みのあるメッシュに変換されます。
7.  **後処理（UV展開、マテリアル適用など）**: フィット調整が完了したメッシュに対して、必要に応じて [`core/uv_tools.py`](core/uv_tools.py) の [`unwrap_uv()`](core/uv_tools.py:1) 関数によるUV展開や、[`core/material_manager.py`](core/material_manager.py) の関数によるマテリアル適用が行われます。これらのステップはオペレーター内で順次呼び出されます。
8.  **シーンへの追加と選択**: 最終的に完成した衣装メッシュオブジェクトが、現在のBlenderシーンのコレクションにリンクされます。ユーザーがすぐに編集できるよう、このオブジェクトが選択され、アクティブオブジェクトとして設定されます。
9.  **結果報告**: 処理の成功または失敗を示すメッセージがBlenderのインフォメーションエディターに表示され、ワークフローが完了します。

このワークフロー全体を通じて、エラーが発生した場合には適切なログ出力とユーザーへのエラー報告が行われ、必要に応じて作成途中のオブジェクトのクリーンアップも試みられます。

## 4. 機能間の連携

Adaptive Wear Generator Proの主要な機能は、[`AWG_OT_GenerateWear`](core/operators.py:19) オペレーターを中心に有機的に連携しています。

1.  ユーザーはUIパネル（`ui/` ディレクトリ内のファイルで定義）を通じて、[`core/properties.py`](core/properties.py) で定義されたプロパティ（[`base_body`](core/properties.py:22), [`wear_type`](core/properties.py:28), [`tight_fit`](core/properties.py:33), [`thickness`](core/properties.py:38) など）を設定します。
2.  ユーザーがUIのボタンをクリックすると、[`AWG_OT_GenerateWear`](core/operators.py:19) オペレーターが実行されます。
3.  オペレーターは、まずこれらのプロパティの値を取得します。
4.  次に、[`core/mesh_generator.py`](core/mesh_generator.py) の [`generate_initial_wear_mesh()`](core/mesh_generator.py:90) 関数を呼び出し、選択された [`wear_type`](core/properties.py:28) と追加設定に基づいて初期メッシュを生成させます。
5.  生成された初期メッシュを受け取ったオペレーターは、[`core/fit_engine.py`](core/fit_engine.py) の [`fit_wear_to_body()`](core/fit_engine.py:30) 関数を呼び出し、このメッシュを素体（[`base_body`](core/properties.py:22)）にフィットさせ、[`thickness`](core/properties.py:38) と [`tight_fit`](core/properties.py:33) の設定を適用させます。
6.  フィット調整が完了した最終的なメッシュオブジェクトは、オペレーターによってBlenderシーンに追加され、ユーザーが確認・編集できるようになります。

この一連の流れを通じて、ユーザーの設定に基づいた衣装が自動的に生成され、素体にフィットした状態でシーンに配置されます。

## 5. その他のモジュール

`core/` ディレクトリには、上記の主要機能以外にも、衣装生成後の後処理や補助的な機能を提供するモジュールが含まれています。

-   [`core/uv_tools.py`](core/uv_tools.py): 生成されたメッシュのUV展開を行うための関数（例: [`unwrap_uv()`](core/uv_tools.py:1)）が含まれています。オペレーターの処理フローの中で、フィット調整後に呼び出されることがあります。
-   [`core/material_manager.py`](core/material_manager.py): 生成されたメッシュにマテリアルを適用するための関数（例: [`apply_basic_material()`](core/material_manager.py:18), [`create_lavender_material()`](core/material_manager.py:44)）が含まれています。オペレーターの処理フローの中で、メッシュ生成・フィット調整後に呼び出されることがあります。
-   [`core/blendshape_manager.py`](core/blendshape_manager.py): 素体から衣装へのブレンドシェイプ（シェイプキー）転送に関連する機能（例: [`transfer_blendshapes()`](core/blendshape_manager.py:1)）が含まれています。これは衣装生成後の追加処理として利用される可能性があります。
-   [`core/bone_rigging.py`](core/bone_rigging.py): 衣装にボーンウェイトを転送するなど、リギングに関連する機能（例: [`rig_basic_garment()`](core/bone_rigging.py:1)）が含まれています。これも衣装生成後の追加処理として利用される可能性があります。
-   [`core/export_tools.py`](core/export_tools.py): 生成された衣装を外部ファイル形式（例: FBX）としてエクスポートするための機能（例: [`export_to_fbx()`](core/export_tools.py:4)）が含まれています。
-   `services/`: ロギングサービス (`services/logging_service.py`) やVRChat関連ユーティリティ (`services/vrc_utils.py`) など、アドオン全体で利用される共通サービスが含まれています。

これらのモジュールは、主要な生成・フィット処理の後に追加の処理を実行したり、アドオンの他の部分から呼び出されたりすることで、アドオン全体の機能を提供しています。

---

このガイドが、Adaptive Wear Generator Proのコードベースを理解し、開発を進める上での助けとなれば幸いです。