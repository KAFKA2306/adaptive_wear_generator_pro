# 使用方法

AdaptiveWear Generator Proは、Blender上で編集対象の衣装メッシュ候補を生成する研究用アドオンです。生成直後のメッシュを完成衣装やVRChat対応済み成果物として扱わないでください。

## 対応環境

`src/adaptive_wear_generator_pro/__init__.py`の`bl_info`では次を宣言しています。

- アドオン版: `4.1.1`
- 最低Blender: `4.1.0`
- 表示場所: `View3D > Sidebar > AdaptiveWear`

CIはBlender `4.1.0`で実行されています。

## インストール

1. このリポジトリを取得する
2. `src/adaptive_wear_generator_pro/`をBlenderのaddonsディレクトリへ`adaptive_wear_generator_pro`として配置する、または同ディレクトリをトップレベルに含むZIPを作る
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

現行の衣装タイプは`T_SHIRT`, `PANTS`, `BRA`, `SOCKS`, `GLOVES`, `SKIRT`です。

## 成功・失敗の意味

生成成功条件は`src/adaptive_wear_generator_pro/core_operators.py`の`AWGP_OT_GenerateWear`にあります。runtime monkey-patchは使いません。

要求された後処理について、少なくとも次の事後状態が成立しない場合は`CANCELLED`になります。

- 生成物がMESHである
- material slotが存在する
- `enable_cloth_sim=true`ならCLOTH modifierが存在する
- `auto_rigging=true`なら対象Armature modifierが存在する

`FINISHED`は完成衣装の品質合格を意味しません。FBX、Unity、VRChatクライアントの検証は別工程です。

## 診断機能

`Diagnose Bones & Vertex Groups`は、頂点グループ、ボーン、孤立頂点、n-gon、non-manifold edgeを診断します。non-manifold edgeはBMeshの`edge.is_manifold`で直接確認します。

## 生成後に最低限見るもの

- 意図した部位に衣装メッシュが存在するか
- 面・頂点が崩壊していないか
- マテリアルが意図どおりか
- アーマチュア参照とウェイトが妥当か
- 必要なShape Keyが失われていないか
- 基本ポーズで重大な貫通がないか

正式な成功条件は[VALIDATION.md](VALIDATION.md)を参照してください。
