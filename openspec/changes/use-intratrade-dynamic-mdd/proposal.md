## Why

動態複利的回切判斷使用逐筆淨值高點，但 MDD 報表只使用每週抽樣淨值，可能出現回切次數顯示曾超過 20% 而 MDD(%) 仍低於 20% 的矛盾。MDD 顯示應與回切風險判斷採用相同的逐筆淨值路徑，讓使用者能直接核對觸發原因。

## What Changes

- 動態複利的 MDD(%)、MDD 金額及其日期改由逐筆浮動淨值計算。
- 每週與每月調整模式皆採相同的逐筆 MDD 定義。
- Equity Curve 仍維持每週抽樣，避免改變既有圖表密度與比較方式。
- 補充測試，驗證同一週內的高點與低點會納入 MDD。

## Capabilities

### New Capabilities

無。

### Modified Capabilities

- `dynamic-compounding-analysis`: 將動態複利 MDD 的計算基準由每週抽樣淨值改為逐筆浮動淨值，曲線輸出仍維持每週抽樣。

## Impact

- 後端：`backend/services/dynamic_compounding.py` 的 MDD 計算。
- 測試：`backend/tests/test_dynamic_compounding.py` 的 MDD 取樣預期。
- API 欄位名稱與資料結構不變，但既有專案重新分析後的 MDD 數值與日期可能改變。
