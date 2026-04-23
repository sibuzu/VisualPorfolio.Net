## 1. Beta Deployment Baseline

- [x] 1.1 建立 `docker/visual-portfolio-beta` 目錄與基礎部署檔，複製正式部署必要設定並保留最小差異。
- [x] 1.2 設定 beta 環境參數（含站點識別、API 路由、必要 env）並確認不覆蓋正式環境變數。
- [x] 1.3 將 beta persistent storage 掛載到 `data-beta`，並加入啟動前路徑檢查避免誤用正式資料路徑。

## 2. Domain and Routing

- [x] 2.1 新增 `visualporforlio-beta.sibuzu.com` 的 DNS 記錄與反向代理設定。
- [ ] 2.2 驗證 beta 子網域流量僅導向 beta stack，並確認不會導向正式 stack。
- [x] 2.3 新增/更新健康檢查與 smoke test，驗證 beta 首頁與核心 API 可用。

## 3. Data Isolation Verification

- [ ] 3.1 在 beta 執行上傳與分析流程，確認所有產生資料寫入 `data-beta`。
- [ ] 3.2 驗證 beta 操作不影響正式 `data` 目錄與正式資料庫。
- [x] 3.3 文件化 beta 資料清理與保留策略（頻率、責任人、回收方式）。

## 4. Release Process Gate

- [x] 4.1 定義 beta 驗證清單（功能一致性、健康檢查、關鍵流程）並放入發布文件。
- [x] 4.2 在發布流程加入 beta 驗證必經關卡（手動或 CI gate），未通過時禁止正式上線。
- [x] 4.3 建立 rollback 操作說明（beta 部署失敗時的 DNS/代理/容器回退步驟）。
