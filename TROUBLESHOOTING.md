# AdaptiveWear Generator Pro アドオン サイドバーが表示されない問題のトラブルシューティング

## 問題

Blender の 3D ビューポートのサイドバー（N キーで表示）に「AdaptiveWear」パネルが表示されない。

## 原因

アドオンのエントリーポイントである `__init__.py` ファイルの `register()` 関数と `unregister()` 関数内で、UI 要素（パネルやオペレーター）が定義されている `ui` モジュールの登録・登録解除処理が呼び出されていなかった。

Blender アドオンでは、`__init__.py` の `register()` 関数がアドオン有効化時に実行され、アドオン内のすべてのクラス（プロパティグループ、パネル、オペレーターなど）を Blender に登録する必要がある。同様に、`unregister()` 関数でこれらのクラスの登録を解除する必要がある。

当初の `__init__.py` では、`core.properties.AdaptiveWearProps` の登録のみが行われており、`ui` モジュール内のパネルやオペレーターが登録されていなかったため、サイドバーにパネルが表示されなかった。

## 解決策

`__init__.py` ファイルの `register()` 関数と `unregister()` 関数に、`ui` モジュールの登録・登録解除処理を追加する。

具体的には、以下の変更を `__init__.py` に適用した。

```diff
--- a/__init__.py
+++ b/__init__.py
@@ -20,9 +20,11 @@
 )

 def register():
     for cls in classes:
         bpy.utils.register_class(cls)
     bpy.types.Scene.adaptive_wear_props = PointerProperty(type=AdaptiveWearProps)
+    ui.register()

 def unregister():
-    del bpy.types.Scene.adaptive_wear_props
+    ui.unregister()
     del bpy.types.Scene.adaptive_wear_props
     for cls in reversed(classes):
         bpy.utils.unregister_class(cls)

```

### 修正手順

1.  `__init__.py` ファイルを開く。
2.  `register()` 関数内に `ui.register()` を追加する。
3.  `unregister()` 関数内に `ui.unregister()` を追加する。
4.  Blender でアドオンを無効化し、再度有効化して変更を適用する。

この修正により、アドオン有効化時に UI パネルやオペレーターが正しく登録され、サイドバーに「AdaptiveWear」パネルが表示されるようになる。

## 確認方法

1.  Blender を起動する。
2.  「Edit」→「Preferences」→「Add-ons」タブを開き、「AdaptiveWear Generator Pro」アドオンが有効になっていることを確認する。
3.  3D ビューポートで N キーを押してサイドバーを表示し、「AdaptiveWear」タブが表示されていることを確認する。