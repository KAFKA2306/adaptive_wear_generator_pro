# AdaptiveWear Generator Pro — Blender衣装候補生成アドオン

[![CI for AdaptiveWear Generator Pro](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/awg-pro-ci.yml/badge.svg)](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/awg-pro-ci.yml)
[![Strict generation contract](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/strict-generation-contract.yml/badge.svg)](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/strict-generation-contract.yml)

Blender上の素体メッシュから、編集開始点となる衣装メッシュ候補を生成する研究用アドオンです。

## 現在の位置づけ

**生成物を完成衣装、販売品質、Unity/VRChat対応済み成果物として扱わないでください。**

現行実装はBlender Python APIを使ったルールベース処理です。学習済みモデル、推論ランタイム、学習データ、モデル版はありません。`AI`を含む旧クラス名・プロパティ名は互換性のため残っています。

## 現行実装

- アドオン版: `4.1.1`
- 最低Blender: `4.1.0`
- パネル: `3D Viewport > Sidebar > AdaptiveWear`
- 衣装タイプ: `T_SHIRT`, `PANTS`, `BRA`, `SOCKS`, `GLOVES`, `SKIRT`
- 生成: `core_generators.py`
- 生成オーケストレーションとfail-closed契約: `core_operators.py`
- マテリアル: `core_materials.py`
- リギング・クロス補助: `core_utils.py`
- UI: `ui_panels.py`

`AWGP_OT_GenerateWear`は、マテリアル、要求されたCloth modifier、要求されたArmature modifierを処理後のBlender状態で確認し、成立しない場合は`CANCELLED`を返します。runtime monkey-patchは使いません。

## 自動検証

Blender 4.1 CIで次を実行します。

- 6衣装タイプの基本生成
- T-Shirt / Pants / Skirtのメッシュ整合性
- T-ShirtのFBX書き出し → 空シーンへ再読込
- strict generation contractの静的契約テスト

FBX round-tripはBlender標準exporter/importer内の検証です。Unity、VRChat SDK、VRChatクライアントは未検証です。

## 既知の品質境界

- 実アバターへのフィット品質・ポーズ貫通は未検証
- UV・テクスチャ・Shape Keyの意味的互換は未検証
- Unity / VRChat SDK / VRChatクライアントは未検証
- `AI`を含む旧名称がUI・プロパティに残る

## ドキュメント

- [使用方法](docs/USAGE.md)
- [実装構造](docs/ARCHITECTURE.md)
- [検証と成功条件](docs/VALIDATION.md)
- [docsの管理方針](docs/README.md)

開発予定・未解決事項はGitHub Issuesを正本とします。`docs/task*.md`のような別タスクリストは作りません。

## 最小実行手順

1. リポジトリをBlenderアドオンとして配置またはZIP化する
2. Blenderで`AdaptiveWear Generator Pro`を有効化する
3. `3D Viewport > Sidebar > AdaptiveWear`を開く
4. 検証用に複製した素体メッシュを指定する
5. 衣装タイプと必要な設定を選び、`Generate Wear`を実行する
6. `FINISHED`だけで品質合格とせず、[検証と成功条件](docs/VALIDATION.md)に従って成果物を検査する

元の`.blend`、Prefab、アバター、衣装データは別途バックアップしてください。第三者の購入アセットを公開リポジトリへ含めないでください。

## 開発上の正本

| 対象 | 正本 |
| --- | --- |
| アドオンの能力 | `main`のPython実装 |
| UI設定 | `core_properties.py`, `ui_panels.py` |
| 生成成功条件 | `core_operators.py` |
| 自動テスト | `tests/`, `.github/workflows/` |
| 未解決事項 | GitHub Issues |
| 利用・設計・検証説明 | `docs/` |

コードと文書が矛盾する場合はコードと実行結果を優先し、文書を修正してください。
