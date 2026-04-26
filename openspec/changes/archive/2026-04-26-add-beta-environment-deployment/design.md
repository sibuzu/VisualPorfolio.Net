## Context

目前部署流程以正式環境為主，缺少一個常設 beta 站點，導致部署前只能在本地或臨時環境驗證。需求要求建立 `visualporforlio-beta.sibuzu.com`，且 beta 必須與正式站功能一致但資料與部署資源隔離。現有專案結構已包含 `docker/visual-portfolio` 相關部署資源，適合複製並參數化出 `docker/visual-portfolio-beta`。

## Goals / Non-Goals

**Goals:**
- 提供可對外訪問的 beta 網址 `visualporforlio-beta.sibuzu.com`。
- 建立與正式環境分離的部署配置與資料目錄（`data-beta`）。
- 讓 beta 可執行與正式站相同功能，用於上線前驗證。
- 將 beta 驗證納入發布流程，形成「beta 通過才可上正式」的作業規範。

**Non-Goals:**
- 不在本變更中修改策略計算邏輯或功能內容。
- 不在本變更中重構整體 CI/CD 平台。
- 不強制引入新雲服務供應商或容器編排系統。

## Decisions

1. 採用獨立 docker 目錄 `docker/visual-portfolio-beta` 作為 beta 的部署入口。
- Rationale: 與正式配置物理分離，降低誤用正式環境參數風險。
- Alternative: 單一 compose 以 profile 區分。此法可減少檔案，但增加操作失誤風險與排錯複雜度。

2. 採用獨立資料根目錄 `data-beta`。
- Rationale: 清楚隔離檔案、資料庫與上傳內容，防止測試資料污染正式資料。
- Alternative: 同目錄不同 DB 檔名。仍有檔案與附件混用風險。

3. 發布流程新增 beta 驗證關卡（手動或自動檢查）後才允許正式部署。
- Rationale: 將「先 beta 測通」落為明確流程，而非口頭約定。
- Alternative: 僅文件約定不做流程檢查。難以一致執行。

## Risks / Trade-offs

- [DNS/反向代理設定錯誤導致 beta 無法訪問] → 以 smoke test 驗證域名解析與健康檢查路由。
- [beta 與正式配置漂移，功能不一致] → 建立共享環境變數模板與定期比對清單。
- [操作人員誤連正式資料目錄] → 在 beta 啟動腳本與 compose 中硬性指定 `data-beta`，並加入啟動時路徑檢查。
- [新增一套部署配置增加維護成本] → 以最小差異策略維護（僅域名、資料路徑、必要環境參數不同）。

## Migration Plan

1. 建立 `docker/visual-portfolio-beta` 配置並設定資料掛載到 `data-beta`。
2. 配置 `visualporforlio-beta.sibuzu.com` 的 DNS 與反向代理路由。
3. 啟動 beta stack，執行健康檢查與基本功能 smoke test。
4. 建立發布檢查清單：beta 驗證通過紀錄為正式發布前置條件。
5. Rollback: 若 beta 部署失敗，回退 beta 相關 DNS/代理設定與容器版本，不影響正式站。

## Open Questions

- beta 站是否需要獨立使用者驗證資料（例如分離 guest/admin 帳號資料）？
- beta 驗證關卡要以 CI 自動化檢查實現，或先以手動 checklist 過渡？
- beta 資料保留與清理策略（例如每週清理、版本切換清理）要採哪一種？
