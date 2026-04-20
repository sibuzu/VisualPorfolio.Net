## Why

現有分析頁缺少可調參數的動態複利模擬，使用者無法在同一視圖比較每週/每月調整下的資金成長、回撤與風險控制。這次需要把策略切換規則、結果表格與曲線視覺化標準化，並與既有分析資料流整合。

## What Changes

- 新增主分頁「動態複利」，提供動態複利參數編輯、說明按鈕、結果表格與 Equity Curve 圖。
- 擴充 `/analysis` 請求與回應合約，支援 `dynamic_compounding` 設定與每週/每月模擬結果。
- 後端新增動態複利模擬邏輯，包含加碼切換、回撤切回、恢復再加碼、風險封頂與達到最大倍數日期判定。
- MDD 與曲線統一採用「週浮動淨值抽樣」：不使用每日或每筆交易點，月模式也對齊到相同週節點進行比較與繪圖。
- 前端支援 read-only 專案即時重算（不寫回 DB，刷新後回復原值）。

## Capabilities

### New Capabilities
- `dynamic-compounding-analysis`: 在分析流程中提供可配置的動態複利模擬、標準化 MDD/曲線計算與前端互動展示。

### Modified Capabilities
- 無

## Impact

- Backend:
  - `backend/routers/analysis.py`
  - `backend/services/dynamic_compounding.py`
  - `backend/tests/test_dynamic_compounding.py`
- Frontend:
  - `frontend/src/views/ProjectView.vue`
  - `frontend/src/components/DynamicCompoundingPanel.vue`
  - `frontend/src/stores/portfolio.js`
- API:
  - `/projects/{project_id}/analysis` request options and response payload (`dynamic_compounding`)
