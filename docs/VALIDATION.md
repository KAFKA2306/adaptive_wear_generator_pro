# 検証と成功条件

このリポジトリでは、Blenderオペレーターが`FINISHED`を返すことと、完成衣装として使えることを分けます。

## 1. 生成処理の成功

登録時に`core_safety.install_strict_generation_contract()`が有効になります。要求された後処理が失敗した場合は例外を上位へ伝播し、生成オペレーターは`CANCELLED`を返します。

自動テスト:

```bash
python -m unittest discover -s tests -p "test_strict_generation_contract.py" -v
```

GitHub Actions: `.github/workflows/strict-generation-contract.yml`

この検証が保証するのは、主に「必須後処理の失敗を成功として隠さない」というコード契約です。衣装品質そのものの保証ではありません。

## 2. Blender CI

`.github/workflows/awg-pro-ci.yml`はBlender `4.1.0`を取得し、主に次を実行します。

```bash
blender -b -P tests/run_basic_functionality_test.py -- --output-dir test-results/basic-functionality
blender -b -P tests/run_pleats_quality_test.py -- --output-dir test-results/pleats-quality
blender -b -P tests/run_mesh_integrity_test.py -- --output-dir test-results/mesh-integrity --wear-type T_SHIRT
blender -b -P tests/run_mesh_integrity_test.py -- --output-dir test-results/mesh-integrity --wear-type PANTS
blender -b -P tests/run_mesh_integrity_test.py -- --output-dir test-results/mesh-integrity --wear-type SKIRT
blender -b -P tests/run_visual_regression_test.py -- --output-dir test-renders/current --baseline-dir test-renders/baseline --diff-dir test-renders/diff --wear-types T_SHIRT SKIRT
```

CI成功は、そのworkflowが検査した入力と条件に対する成功です。任意のアバター、任意の衣装タイプ、Unity、VRChatの成功へ一般化しません。

## 3. 現在のCIで不足しているもの

### 真の多様体検査

`AWGP_OT_DiagnoseBones`の`manifold_status`は`bmesh.is_valid`を使っています。これはBMeshデータ構造のvalidityであり、非多様体エッジを直接検査する合格条件ではありません。

### Visual Regressionの正本

現行treeには`test-renders/baseline/`のコミット済み基準画像がありません。workflowは実行時に空ディレクトリを作るため、基準画像が実際に存在し比較できたことをCI結果・artifactで確認するまで、Visual Regressionを品質合格証拠として扱いません。

### Blender版の幅

自動CIはBlender `4.1.0`です。4.4系など他のBlender版は別途実測が必要です。

### 実アバターへの一般化

公開リポジトリのテストは、購入アバターや第三者モデルを正本fixtureとして含めません。対象アバターごとのメッシュ、骨格、ウェイト、Shape Key差は別途確認が必要です。

## 4. 完成衣装として扱うための受入検査

少なくとも次を個別にPASS/FAILで記録してください。

1. 生成オブジェクトが存在し、頂点・面の数値が有限
2. 非多様体エッジ、孤立頂点、ゼロ面積面、反転法線を実検査
3. UVとマテリアルが対象レンダラーで有効
4. アーマチュア参照が正しく、必要な頂点へ有効なウェイトがある
5. 必須Shape Keyの名称・頂点数・変形差分が期待どおり
6. ニュートラル、腕上げ、腕組み、しゃがみ、座り、伏せ等で重大な貫通がない
7. `.blend`保存・再読込後も結果が再現する
8. FBX等の必要形式へ出力し、再読込後も結果が再現する
9. Unityへ読み込み、Prefab/Renderer/Armature/Blend Shapeが期待どおり
10. VRChat SDKビルドが成功する
11. VRChatクライアント内で表示・ポーズ・アニメーション・貫通を確認する
12. 素体・衣装・テクスチャ等の利用許諾を確認する

未確認の項目は`PASS`にせず、`UNVERIFIED`として残します。

## 5. 証拠の扱い

- `test-results/`の既存ファイルは過去の実行記録であり、現在のmainや任意入力の合格証拠ではありません
- GitHub Actionsは対象commit SHAとworkflow runを対応付けて確認します
- PRではPR head SHAのCIを確認し、merge後はmainのcommitをread-backします
- Blender外の品質を主張する場合は、Unity/VRChat等の実環境結果を別証拠として残します
- 警告を成功へ読み替えません。プリーツ品質スコア70未満は現在、警告であって自動FAILではありません

## 6. 未実装の検証はIssueへ

検証要件や改善案を`docs/task*.md`へ追加しません。再現条件、期待結果、完了条件をGitHub Issueとして管理し、実装後にこの文書の「現在の検証範囲」だけを更新します。