# 靴下と手袋のメッシュ生成機能実装計画

## 目標

`AdaptiveWearProps` を拡張し、`AWGP_OT_GenerateWear` オペレーターに靴下と手袋のメッシュ生成機能を追加する。

## 計画詳細

1.  **設計とプロパティ追加:**
    *   靴下と手袋のメッシュ生成に必要な頂点グループ（例: "foot", "leg", "hand", "arm"）と、固有のパラメータ（靴下の長さ、手袋の指あり/なし）を具体的に定義する。
    *   これらの固有パラメータを [`core/properties.py`](core/properties.py) の `AdaptiveWearProps` クラスに追加します。
        *   靴下の長さ (`socks_length`): EnumProperty (例: 'ankle', 'calf', 'knee')
        *   手袋の指あり/なし (`gloves_fingered`): BoolProperty
2.  **UIパネルの更新:**
    *   [`ui/panel_main.py`](ui/panel_main.py) の `AWGP_PT_MainPanel` に、靴下と手袋の固有パラメータを設定するためのUI要素を追加します。
    *   衣装タイプが「靴下」または「手袋」の場合にのみこれらのUI要素が表示されるように、`draw` メソッド内に条件分岐を追加します。
3.  **オペレーターロジックの更新:**
    *   [`core/operators.py`](core/operators.py) の `AWGP_OT_GenerateWear` オペレーターの `execute` メソッドを修正します。
    *   衣装タイプが「靴下」または「手袋」の場合に、適切な頂点グループを検索し、UIから固有パラメータを取得します。
    *   取得した頂点グループとパラメータを、[`core/mesh_generator.py`](core/mesh_generator.py) の `create_socks_mesh` または `create_gloves_mesh` 関数に渡すように関数呼び出しを修正します。
4.  **メッシュ生成ロジックの実装:**
    *   [`core/mesh_generator.py`](core/mesh_generator.py) の `create_socks_mesh` 関数と `create_gloves_mesh` 関数に、素体の該当部分を基にしたメッシュ生成ロジックを実装します。これには、素体メッシュのコピー、頂点グループによるフィルタリング、形状調整（フィット感、厚み、長さ、指の有無など）、スムーズシェード、モディファイアのコピーなどが含まれます。
5.  **テストと調整:**
    *   実装した機能が正しく動作するかテストし、必要に応じて調整を行います。

## 想定される成果物

*   [`core/properties.py`](core/properties.py) の `AdaptiveWearProps` に靴下と手袋の固有パラメータが追加される。
*   [`ui/panel_main.py`](ui/panel_main.py) の `AWGP_PT_MainPanel` に靴下と手袋の固有設定UIが追加される。
*   [`core/operators.py`](core/operators.py) の `AWGP_OT_GenerateWear` オペレーターが靴下と手袋の生成に対応する。
*   [`core/mesh_generator.py`](core/mesh_generator.py) の `create_socks_mesh` および `create_gloves_mesh` 関数に実際のメッシュ生成ロジックが実装される。

---

この計画に基づき、Codeモードに切り替えて実装作業を開始します。