# AdaptiveWear Generator Pro — Blender密着衣装生成アドオン

[![CI for AdaptiveWear Generator Pro](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/awg-pro-ci.yml/badge.svg)](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/awg-pro-ci.yml)
[![Strict generation contract](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/strict-generation-contract.yml/badge.svg)](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/strict-generation-contract.yml)

Blender上の素体メッシュから、Tシャツ、パンツ、ブラ、靴下、手袋、プリーツスカートの候補形状を生成するアドオンです。

## 現在の状態：研究候補のみ

**販売、Unity納品、VRChat実装、image2outfitの正式候補生成へ接続しないでください。** コード監査で、成功判定と品質表示に未修正の問題を確認しています。

### 確認した阻害要因

- 実装内に学習済みモデル、推論ランタイム、学習データ、モデル版が見当たらず、`AI`は名称だけのルールベース処理
- `OptimizedAIWearGenerator`、`AI品質モード`、`AI閾値`等の名称が実装能力を過大表示
- マテリアル、クロス、リギング等のポスト処理例外を`_apply_post_processing`で捕捉・ログ出力した後、オペレーターが`FINISHED`を返す
- リギング失敗、アーマチュア未検出、ウェイト転送失敗を最終成功条件へ反映しない
- プリーツ品質スコアが70未満でも警告だけで成功
- メッシュ診断の`bm.is_valid`を多様体判定として表示しているが、非多様体エッジ検査ではない
- 厚みを「メートル」と表示する一方、シーン単位・オブジェクトスケールの受入検査がない
- `preserve_shapekeys`等の設定名が、全Shape Keyの意味的互換・完全転送を保証するように見える
- Blender内生成成功と、Unity/VRChatでの動作・貫通・権利確認が分離されていない

これらを修正するまでは、生成物を「自動完成衣装」ではなく**編集対象のメッシュ候補**として扱います。

## 実装上の実態

現在確認できる処理は、Blender Python APIによる手続き的な形状抽出・モディファイア・頂点グループ・マテリアル・リギング補助です。

- 素体メッシュを入力とするルールベース候補生成
- Shrinkwrap系の形状追従
- Solidify等による厚み
- 頂点グループ・Data Transfer系の補助
- ルールベースの衣装タイプ別領域選択
- マテリアルプリセット
- ボーン・頂点グループ診断
- プリーツ形状評価

AIによる品質判定、トポロジ汎化、学習済み変形モデル、知覚評価モデルは確認できません。

## 対応環境

```text
bl_info version: 4.1.0
最低Blender: 4.1.0
推奨監査環境: Blender 4.4系
```

## インストールと実行

1. リポジトリをアドオンとして配置またはZIP化する
2. Blenderの`編集 > プリファレンス > アドオン`から有効化する
3. `3D Viewport > Sidebar > AdaptiveWear`を開く
4. 複製した検証用素体を指定する
5. 衣装候補を生成する
6. ログだけでなく成果物を検査する

元の素体・Prefab・Blendファイルをバックアップしてください。

## 正式成功条件

`FINISHED`が返るだけでは合格にしません。少なくとも次をすべて別々に検証する必要があります。

1. 生成オブジェクトが存在し、頂点・面が有限
2. 非多様体、孤立頂点、ゼロ面積面、反転法線を検査
3. UVとマテリアルが対象レンダラーで有効
4. アーマチュア参照と全ウェイトが有効
5. 必須Shape Keyの数・名称・頂点数が一致
6. ニュートラル、腕上げ、腕組み、しゃがみ、座り、伏せで貫通検査
7. Blender保存・再読込後も再現
8. FBX出力・Unity読込後も再現
9. VRChat SDKビルドとクライアント内確認
10. 対象素体と衣装の利用許諾を確認

## 修正すべきコード契約

- ポスト処理の例外を握りつぶさず、必須工程失敗時は`CANCELLED`
- `GenerationResult`へ各工程のPASS/FAILと証拠パスを保存
- アーマチュアなしで`auto_rigging=true`なら失敗
- シーン単位・適用済みスケールを事前検査
- 真の非多様体検査を実装
- `AI`表記を`heuristic`または`rule_based`へ変更
- Shape Keyは「完全継承」ではなく、件数・頂点対応・差分を検査
- Blender、Unity、VRChatの各ゲートを分離

## 主な構成

```text
__init__.py
core_properties.py
core_operators.py
core_generators.py
core_utils.py
ui_panels.py
tests/
test-results/
docs/
```

既存の`test-results/`は過去の記録であり、現在の環境や任意のアバターでの合格を意味しません。

## 注意

- 購入アバターや第三者モデルを公開リポジトリへ含めないでください
- Blender生成成功を販売品質と同一視しないでください
- `AI駆動`、`最高品質`、`完全継承`という表示は現在の実装証拠と一致しません
- 正式衣装制作は`image2outfit`側の候補生成・品質ゲート・人間レビューを正とします

**README最終監査:** 2026-08-02