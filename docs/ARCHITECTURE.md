# AdaptiveWear Generator Pro アーキテクチャ

## ファイル・フォルダ構造

```
.
├── __init__.py             # アドオンのエントリーポイント、登録/登録解除処理
├── README.md               # プロジェクト概要、インストール、基本的な使い方
├── tasks.md                # 開発タスクリスト
├── ARCHITECTURE.md         # アーキテクチャ設計ドキュメント
├── core/                   # コアロジックモジュール
│   ├── __init__.py
│   ├── bone_brendshape_weight_transfer.py  # ボーンリギング、ブレンドシェイプ統合処理
│   ├── fit_engine.py       # メッシュフィッティングエンジン
│   ├── material_generator.py # マテリアル生成・適用
│   ├── mesh_generator.py   # メッシュ生成（衣装タイプ別）
│   ├── operators.py        # Blenderオペレーター定義
│   ├── properties.py       # Blenderプロパティグループ定義
│   └── weight_transfer.py  # ウェイト転送処理
├── ui/                     # ユーザーインターフェースモジュール
│   ├── __init__.py
│   └── panel_main.py       # メインUIパネル
├── services/               # 共通サービスモジュール
│   ├── __init__.py
│   └── logging_service.py  # ロギングサービス
└── presets/                # プリセットデータ
    └── materials.json      # マテリアルプリセット定義
```

## 各部分の役割

### **ルートレベル**

- **`__init__.py`**:
  - Blenderがアドオンとして認識するための必須ファイル
  - アドオンメタデータを定義（`bl_info`）
  - 全クラスの一括登録・登録解除処理
  - シーンプロパティの設定・削除
  - ロギングサービスの初期化

### **core/（コアロジック）**

- **`properties.py`**:
  - `AdaptiveWearGeneratorProPropertyGroup`クラス定義
  - 素体選択、衣装タイプ、フィット設定などのプロパティ
  - 衣装タイプ別の追加プロパティ（靴下の長さ、手袋の指など）

- **`operators.py`**:
  - `AWGP_OT_GenerateWear`オペレーター定義
  - 衣装生成の全工程を統括（入力検証→メッシュ生成→フィッティング→リギング→マテリアル適用）
  - エラーハンドリングとクリーンアップ処理

- **`mesh_generator.py`**:
  - 衣装タイプ別メッシュ生成関数
  - 頂点グループベースの範囲選択
  - bmeshを使用した編集処理
  - Solidifyモディファイアによる厚み追加

- **`fit_engine.py`**:
  - Shrinkwrapモディファイアを使用したフィッティング処理
  - tight_fit設定に基づくフィッティングモード切り替え
  - 素体への密着度調整

- **`weight_transfer.py`**:
  - Data Transferモディファイアを使用したウェイト転送
  - 素体から衣装への頂点グループ重みコピー
  - 選択状態の保存・復元

- **`bone_brendshape_weight_transfer.py`**:
  - アーマチュアモディファイア設定
  - ウェイト転送処理の統合呼び出し
  - ブレンドシェイプ（シェイプキー）転送処理
  - Surface Deformモディファイアを使用した形状変形転送

- **`material_generator.py`**:
  - Principled BSDFベースのマテリアル作成
  - プリセットJSONファイルからの設定読み込み
  - 衣装タイプ別デフォルトマテリアル
  - Blender 4.x対応のSpecular設定

### **ui/（ユーザーインターフェース）**

- **`panel_main.py`**:
  - `AWG_PT_MainPanel`パネルクラス定義
  - 基本設定、タイプ別設定、フィット設定の段階的表示
  - 動的UIコントロール（衣装タイプに応じた追加オプション表示）
  - 入力検証とエラー表示
  - 生成ボタンの有効/無効制御

### **services/（共通サービス）**

- **`logging_service.py`**:
  - 統一ロギングシステム
  - 情報、警告、エラー、デバッグレベルのログ出力
  - コンソールへの構造化ログ表示
  - 初期化とクリーンアップ処理

### **presets/（プリセットデータ）**

- **`materials.json`**:
  - 衣装タイプ別マテリアル設定
  - 色、透明度、スペキュラー、ラフネス値
  - 拡張可能なJSON形式

## データフローとプロセス

### **1. 初期化フロー**
```
__init__.py → register()
├── classes登録（プロパティ、オペレーター、パネル）
├── シーンプロパティ設定
└── ロギングサービス初期化
```

### **2. 衣装生成フロー**
```
UI Panel → AWGP_OT_GenerateWear
├── 入力検証
├── mesh_generator.generate_wear_mesh()
│   ├── 衣装タイプ別メッシュ生成
│   ├── 頂点グループ選択
│   ├── bmesh編集
│   └── Solidify処理
├── fit_engine.apply_fitting()
│   ├── Shrinkwrapモディファイア追加
│   ├── フィット設定適用
│   └── モディファイア適用
├── bone_brendshape_weight_transfer.apply_rigging()
│   ├── アーマチュア設定
│   ├── weight_transfer.transfer_weights()
│   └── ブレンドシェイプ転送
└── material_generator.apply_wear_material()
    ├── プリセット読み込み
    ├── マテリアル作成
    └── オブジェクトへの適用
```

### **3. エラーハンドリングフロー**
```
各処理段階
├── try-catch例外処理
├── logging_service経由のエラーログ
├── self.report()によるユーザー通知
└── 必要に応じてクリーンアップ処理
```

## 状態管理とデータ連携

### **プロパティ管理**
- **シーンレベル**: `bpy.types.Scene.adaptive_wear_generator_pro`
- **プロパティアクセス**: `context.scene.adaptive_wear_generator_pro`
- **永続化**: Blenderファイルと共に保存

### **オブジェクト間連携**
- **素体→衣装**: メッシュデータ、頂点グループ、アーマチュア
- **アーマチュア→衣装**: ボーン構造、変形設定
- **プリセット→衣装**: マテリアル設定、色彩情報

### **モディファイア連携**
```
生成された衣装オブジェクト
├── Shrinkwrap（フィッティング）
├── Armature（リギング）
└── 最終的にすべて適用
```

## 拡張性とカスタマイゼーション

### **新しい衣装タイプの追加**
1. `properties.py`の`get_wear_types_items()`に項目追加
2. `mesh_generator.py`に対応する生成関数追加
3. `presets/materials.json`にマテリアル設定追加

### **新しいフィッティングアルゴリズム**
- `fit_engine.py`内での新しいモディファイア組み合わせ
- プロパティ追加による設定オプション拡張

### **カスタムマテリアル**
- `presets/materials.json`への新規プリセット追加
- `material_generator.py`での新しいノード構成
