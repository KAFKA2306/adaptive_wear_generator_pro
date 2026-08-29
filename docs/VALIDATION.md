# 検証と成功条件

`FINISHED`は「要求された生成工程が完了した」ことを示し、完成衣装品質を意味しません。

## 1. strict generation contract

`core_operators.AWGP_OT_GenerateWear._apply_post_processing()`が生成成功条件の正本です。runtime monkey-patchはありません。

自動テスト:

```bash
python -m unittest discover -s tests -p "test_strict_generation_contract.py" -v
```

静的契約テストは、後処理メソッドが例外を内部で握り潰さないこと、`core_safety.py`のような別authorityが存在しないこと、Cloth/Armatureの事後条件を検査するコードがあることを確認します。

## 2. Blender 4.1 CI

`.github/workflows/awg-pro-ci.yml`はBlender `4.1.0`で次を実行します。

```bash
blender -b -P tests/run_basic_functionality_test.py -- --output-dir test-results/basic-functionality
blender -b -P tests/run_mesh_integrity_test.py -- --output-dir test-results/mesh-integrity --wear-type T_SHIRT
blender -b -P tests/run_mesh_integrity_test.py -- --output-dir test-results/mesh-integrity --wear-type PANTS
blender -b -P tests/run_mesh_integrity_test.py -- --output-dir test-results/mesh-integrity --wear-type SKIRT
blender -b -P tests/run_fbx_roundtrip_test.py -- --output-dir test-results/fbx-roundtrip
```

`test-results/`はworkflow artifactとして保存し、リポジトリへコミットしません。

## 3. 現在の自動検証範囲

### 基本生成

`T_SHIRT`, `PANTS`, `BRA`, `SOCKS`, `GLOVES`, `SKIRT`を最小fixtureから実生成し、Operatorが`FINISHED`を返し、生成メッシュに頂点と面があることを確認します。

### メッシュ整合性

T-Shirt / Pants / Skirtについて、生成メッシュの頂点・辺・面、有限座標、3頂点以上の面を検査します。

### FBX round-trip

T-ShirtをBlender標準FBX exporterで書き出し、空シーンへ再読込し、再読込後メッシュの頂点・面・有限座標を確認します。生成FBX自体もActions artifactへ保存します。

これはBlender内round-tripであり、UnityやVRChatの互換性を証明しません。

## 4. 未検証

- Blender 4.1.0以外の版
- 実アバターごとのフィット・ウェイト・Shape Key
- 非多様体、孤立頂点、ゼロ面積面、反転法線を全衣装タイプで合格条件化すること
- UV・テクスチャの実レンダラー確認
- ポーズ時の貫通
- Unity import / Prefab / Renderer / Blend Shape
- VRChat SDK build
- VRChatクライアント内表示
- 第三者アセットの個別利用許諾

未確認項目は`PASS`にせず`UNVERIFIED`とします。

## 5. 完成衣装として扱うための受入検査

1. 生成オブジェクトが存在し、頂点・面の数値が有限
2. 非多様体エッジ、孤立頂点、ゼロ面積面、反転法線を実検査
3. UVとマテリアルが対象レンダラーで有効
4. アーマチュア参照とウェイトが有効
5. 必須Shape Keyの名称・頂点数・変形差分が期待どおり
6. ニュートラル、腕上げ、腕組み、しゃがみ、座り等で重大な貫通がない
7. `.blend`保存・再読込後も結果が再現
8. FBX等へ出力し再読込後も結果が再現
9. Unityへ読み込み、Prefab/Renderer/Armature/Blend Shapeを確認
10. VRChat SDKビルド成功
11. VRChatクライアント内で表示・ポーズ・アニメーションを確認
12. 利用許諾を確認

## 6. 証拠の扱い

- GitHub Actionsは対象commit SHAとworkflow runを対応付けて確認する
- PRではexact-head CI、merge後はmain commitのCIを確認する
- workflow artifactは実行時の証拠であり、別commitの合格証拠へ流用しない
- Blender外の品質を主張する場合はUnity/VRChat等の実環境結果を別証拠として残す
- 警告や未実施項目を成功へ読み替えない

検証要件や改善案は`docs/task*.md`へ複製せずGitHub Issuesで管理します。
