## UnderwearProps にあって AdaptiveWearProps にない機能

`UnderwearProps` に存在し、`AdaptiveWearProps` に存在しない機能は、素体オブジェクトを指定するための `base_body` プロパティです。

この `base_body` プロパティは、下着生成機能において、ユーザーがUIで下着を生成したい素体オブジェクトを選択し (`ui/panel_main.py:130` 参照)、その選択されたオブジェクトをオペレーターが取得して処理するために使用されます (`core/operators.py:109` 参照)。

ユーザーからのフィードバックによると、この `base_body` プロパティが `AdaptiveWearProps` に不足していることが、`AdaptiveWearGeneratorPro` アドオンで下着生成が正常に行えない一因となっている可能性があるとのことです。