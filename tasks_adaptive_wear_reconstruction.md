## AdaptiveWearProps 再構成のための小タスクリスト

### 目標

`AdaptiveWearProps` を `UnderwearProps` の完全上位互換とし、`AWGP_OT_GenerateWear` オペレーターが `UNDERWEAR_OT_Generate` オペレーターの機能を包含しつつ、複数衣装タイプ生成などの汎用機能も適切に扱えるようにする。

UIに素体を選ぶボタンを追加
UIに衣装生成ボタンを追加。
それらの機能が連関して機能するように全体をコーディング
### 小タスク

UIに素体を選ぶボタンを追加
UIに衣装生成ボタンを追加。
それらの機能が連関して機能するように全体をコーディング
1.  **`AdaptiveWearProps.base_body` プロパティの確認:**
    *   [`core/properties.py`](core/properties.py) を開き、`AdaptiveWearProps` クラスに `base_body` プロパティが追加されていることを確認する。
    *   もし追加されていなければ、`UnderwearProps` の定義を参考に `base_body: bpy.props.PointerProperty(...)` を追加する。

2.  **`AWGP_OT_GenerateWear` オペレーターの素体取得ロジック修正:**
    *   [`core/operators.py`](core/operators.py) を開き、`AWGP_OT_GenerateWear` クラスの `execute` メソッドを編集する。
    *   `context.active_object` を取得している箇所 (`core/operators.py:21`) を修正し、`context.scene.adaptive_wear_props.base_body` が設定されている場合はそのオブジェクトを、設定されていない場合は `context.active_object` を素体 (`body` 変数) として使用するように変更する。

3.  **パンツ生成時の頂点グループ検索ロジック調整:**
    *   [`core/operators.py`](core/operators.py) の `AWGP_OT_GenerateWear` クラス内で、`self.garment_type == 'pants'` の条件分岐内を編集する。
    *   現在の `find_vertex_group_by_keyword` を使用した検索 (`core/operators.py:36`) を、`UNDERWEAR_OT_Generate` が内部で使用している `core/mesh_generator.py` の `create_underwear_pants_mesh` 関数内の検索ロジックと整合させるか、または `create_underwear_pants_mesh` 関数自体を修正して、オペレーターから渡された頂点グループリストと内部検索を適切に組み合わせるようにする。
    *   （※補足：`core/mesh_generator.py` の `create_underwear_pants_mesh` は現在引数 `vg_names` を受け取っていますが、内部では「hip」/「腰」を決め打ちで検索しています。この点の整理が必要です。）

4.  **パンツ生成時のメッシュ生成関数呼び出し修正:**
    *   [`core/operators.py`](core/operators.py) の `AWGP_OT_GenerateWear` クラス内で、`self.garment_type == 'pants'` の条件分岐内を編集する。
    *   `create_underwear_pants_mesh` 関数呼び出し (`core/operators.py:40`) に、`self.fit_tightly` と `self.thickness` の値を正しく渡すように修正する（現在も渡していますが、ステップ3の頂点グループの扱いの修正と合わせて確認・調整が必要です）。

5.  **パンツ生成後の後処理フロー確認:**
    *   [`core/operators.py`](core/operators.py) の `AWGP_OT_GenerateWear` クラス内で、メッシュ生成後の共通後処理フロー (`core/operators.py:90`-`core/operators.py:93`) が、パンツ生成後にも適切に実行されることを確認する。

6.  **パンツ生成時のマテリアル適用調整:**
    *   `AWGP_OT_GenerateWear` オペレーターで生成されたパンツに、`UNDERWEAR_OT_Generate` と同様のラベンダー色半透明マテリアルを適用できるようにする。
    *   これには以下のいずれか、または組み合わせが考えられる：
        *   `AdaptiveWearProps` にマテリアル指定用のプロパティを追加する。
        *   UIパネルにマテリアル選択UIを追加し、その選択をオペレーターに渡す。
        *   パンツ生成の場合のみ、特定の（ラベンダー色）マテリアルを適用するロジックを `AWGP_OT_GenerateWear` に追加する。
    *   （※補足：どの方法を取るかはユーザーの意向やアドオン全体の設計によりますが、まずはパンツ生成時にラベンダー色マテリアルを適用するロジックを追加するのがシンプルかもしれません。）

7.  **UIパネルへの素体選択UI追加:**
    *   [`ui/panel_main.py`](ui/panel_main.py) を開き、`AdaptiveWearProps.base_body` を設定するための素体選択UI（`layout.prop_search` など）を適切な場所に追加する。

8.  **他の衣装タイプのメッシュ生成ロジック実装:**
    *   [`core/mesh_generator.py`](core/mesh_generator.py) を開き、現在スタブ実装となっている他の `create_*_mesh` 関数（`create_socks_mesh` (`core/mesh_generator.py:183`)、`create_gloves_mesh` (`core/mesh_generator.py:201`)、`create_swimsuit_onesie_mesh` (`core/mesh_generator.py:209`)、`create_swimsuit_bikini_mesh` (`core/mesh_generator.py:217`)、`create_tights_mesh` (`core/mesh_generator.py:225`)）に、実際のメッシュ生成ロジックを実装する。
    *   （※補足：これは大きなタスクであり、各衣装タイプごとにさらに小さなタスクに分割される可能性があります。）
*   

UIに素体を選ぶボタンを追加
UIに衣装生成ボタンを追加。
それらの機能が連関して機能するように全体をコーディング