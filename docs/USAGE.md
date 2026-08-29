# 使用方法

AdaptiveWear Generator Proは、Blender上で編集対象の衣装メッシュ候補を生成する研究用アドオンです。生成直後のメッシュを完成衣装やVRChat対応済み成果物として扱わないでください。

## 対応環境

`__init__.py`の現行`bl_info`では次を宣言しています。

- アドオン版: `4.1.1`
- 最低Blender: `4.1.0`
- 表示場所: `View3D > Sidebar > AdaptiveWear`

CIはBlender `4.1.0`で実行されています。4.4系で利用する場合も、実際の入力データで再検証してください。

## インストール

1. このリポジトリを取得する
2. `__init__.py`がアドオンのルートになる形でBlenderへ配置またはZIP化する
3. Blenderのアドオン設定から`AdaptiveWear Generator Pro`を有効化する
4. `3D Viewport > Sidebar > AdaptiveWear`を開く

元データを直接作業対象にせず、検証用に複製した`.blend`と素体を使ってください。

## 基本操作

1. `素体メッシュ`にMESHオブジェクトを指定する
2. `衣装タイプ`を選ぶ
3. 必要なら`詳細設定`を変更する
4. `Generate Wear`を実行する
5. 生成されたオブジェクトとシステムコンソールを確認する
6. [VALIDATION.md](VALIDATION.md)の検証を行う

現行の衣装タイプは次の6種類です。

- `T_SHIRT`
- `PANTS`
- `BRA`
- `SOCKS`
- `GLOVES`
- `SKIRT`

## 主な設定

### 基本設定

- `base_body`: 素体メッシュ
- `wear_type`: 衣装タイプ
- `quality_level`: 品質レベル。旧来の`AI最高品質`表示を含みますが、学習済みAIモデルの利用を意味しません

### フィッティング

- `tight_fit`
- `thickness`
- `progressive_fitting`

`thickness`はUI上でメートル単位と説明されていますが、現状はシーン単位とObject Scaleの受入検査がありません。数値だけを実寸保証として扱わないでください。

### 後処理

- `enable_cloth_sim`
- `enable_edge_smoothing`
- `preserve_shapekeys`
- `use_vertex_groups`
- `min_weight`
- `auto_rigging`

`preserve_shapekeys`は設定名であり、全Shape Keyの意味的互換や完全転送を保証しません。

### 衣装別設定

- 靴下: `sock_length`
- 手袋: `glove_fingers`
- プリーツスカート: `skirt_length`, `pleat_count`, `pleat_depth`

### 旧来のAI名称

`ai_quality_mode`, `ai_threshold`, `ai_subdivision`など、`AI`を含む設定名が残っています。現行リポジトリには学習済みモデル、推論ランタイム、学習データ、モデル版がなく、これらはルールベース生成の調整値です。

## 成功・失敗の意味

生成オペレーターは、入力検証や生成に失敗すると`CANCELLED`を返します。

登録時には`core_safety.install_strict_generation_contract()`が有効になり、要求された後処理について次をfail-closedで扱います。

- 生成物がMESHでない
- マテリアル適用が失敗した
- クロスシミュレーション設定が失敗した
- `auto_rigging=true`なのにアーマチュアが見つからない
- リギング転送が失敗した

ただし、`FINISHED`は完成衣装の品質合格を意味しません。プリーツ品質スコア70未満は現在も警告だけです。FBX、Unity、VRChatクライアントの検証も別工程です。

## 診断機能

`Diagnose Bones & Vertex Groups`で、頂点グループ、ボーン、孤立頂点、n-gon等の診断ログを出せます。

注意: 現在の`manifold_status`は`bmesh.is_valid`を使っており、非多様体エッジを直接検査するものではありません。多様体合格判定として使わないでください。

## 生成後に最低限見るもの

- 意図した部位に衣装メッシュが存在するか
- 面・頂点が崩壊していないか
- マテリアルが意図どおりか
- アーマチュア参照とウェイトが妥当か
- 必要なShape Keyが失われていないか
- 基本ポーズで重大な貫通がないか

正式な成功条件は[VALIDATION.md](VALIDATION.md)を参照してください。