# VisualPortfolio.Net 使用手冊

VisualPortfolio.Net 是策略組合報表（Visual Portfolio）的網路版，提供「免安裝、可分享連結、可與桌面版互通」的使用方式。

## 1. 系統特色

1. 網頁即開即用：<https://visualportfolio.sibuzu.com/>
2. 專案可直接分享：例如 <https://visualportfolio.sibuzu.com/projects/VP-ZDEMOZ>
3. Desktop VisualPortfolio 可直接下載/上傳網路版專案資料。
4. 專案資料若超過 72 小時未被存取，系統會自動清理（`admin` 專案不清理）。

## 2. 帳號與權限

### 2.1 帳號類型

- 一般使用者：可建立、編輯、刪除自己的專案。
- 訪客 `guest`：可由 project 連結進入瀏覽，但不可建立/上傳/複製專案。
- 管理者 `admin`：獨立 `/admin` 登入流程，用於維運管理。

### 2.2 保留名稱

- `admin`、`guest` 不能註冊為一般帳號。

### 2.3 路由行為

- 直接開 `/projects/{project-id}`：未登入時可自動以 `guest` 瀏覽。
- 開 `/`（首頁）未授權：會導向 `/login`，登入後依 redirect 回原頁。
- `/admin`：不受 guest 限制，進頁後會走 admin 密碼驗證。

## 3. 快速上手流程

1. 打開 <https://visualportfolio.sibuzu.com/>。
2. 第一次使用會進入 Login / Sign up。

![login](../img/login.png)

3. 點 `Sign up` 建立帳號後登入。
4. 進入主頁。

![main](../img/main.png)

5. 建立新專案，或從專案列表開啟既有專案。
6. 進入專案頁後，上傳 `.srp/.xrp`，即可看右側分析分頁。

![project](../img/project.png)

## 4. 專案頁操作說明

### 4.1 可編輯 / 可檢視

- 若是專案 owner，會顯示 `（可編輯）`。
- 非 owner 會顯示 `（可檢視）`。

### 4.2 分享連結

- 點 project-id 旁的連結 icon 可複製 project URL。
- 將 URL 分享給他人後，對方可直接檢視該專案。

### 4.3 可編輯模式

- 可新增/刪除策略。
- 可調整啟動、顏色、口數（Count）、權重。
- 可調整分潤退傭 Config。
- 調整會儲存到 server。

### 4.4 可檢視模式

- 不可新增策略。
- 不可刪除策略。
- 但可調整下列項目做「本次視覺化試算」：
  - 啟動
  - 顏色
  - 口數
  - 權重
  - 分潤退傭 Config
- 上述修改不會寫入 server，重新整理後會回復原值。

### 4.5 複製專案

- 在可檢視模式也可按「複製專案」（guest 除外）。
- 複製後會建立新 project-id，owner 變成目前登入者，並開新頁進入新專案。
- 複製後新專案即為可編輯。

## 5. 分析分頁說明

### 5.1 獲利報表（Summary）

- 顯示期間、交易次數、總獲利、年獲利、MDD、Sharpe、Sortino、獲利因子等。
- 下方包含：
  - MDD 明細表
  - Annual Profits 表
  - Month Profits 表

### 5.2 獲利曲線

![獲利曲線](../img/獲利曲線.png)

- 類別可切換：
  - 總獲利
  - 個別獲利
  - 總獲利+個別獲利
- 系統會自動做點數壓縮，避免曲線點過多造成效能問題。

### 5.3 逐年獲利

![逐年獲利](../img/逐年獲利.png)

- 類別可切換：獲利 / 獲利+MDD / 獲利(個別)
- 範圍可切換：每年、每半年、每4月、每3月、每2月、每月

### 5.4 贏輸分析

![贏輸分析](../img/贏輸分析.png)

- 以表格顯示 `日/週/月/年` 的統計：
  - 總次數、贏錢次數、輸錢次數、勝率
  - 平均每次贏錢/輸錢
  - 最大贏錢/輸錢
  - 每次贏輸比、全部贏輸比

### 5.5 分潤退傭

<img src="../img/分潤退傭.png" alt="分潤退傭" style="zoom:50%;" />

- 上方 14 個 Config 參數可調整。
- 下方顯示年度與季度明細（季初資金、季末資金、獲利、分潤、客戶淨獲利、手續費退傭）。

### 5.6 多樣性分析

![多樣性分析](../img/多樣性分析.png)

- 指標卡片：N、N_eff、EER、RDR、DCI、ISN、DSN。
- 明細表：各策略成交占比、交易次數、平均交易金額、平均相關性。

## 6. Desktop VisualPortfolio 上傳 / 下載

請使用 `VisualPortfolio.exe v26.03.17.23964` 以上版本，會新增上傳/下載按鈕。

![vp](../img/vp-desktop.png)

### 6.1 上傳（Desktop -> Net）

![vp-upload](../img/vp-upload.png)

- 上傳需要登入帳號。
- 建議使用與網頁相同帳號，才能在自己的專案列表看到資料。
- 上傳規則：
  - 若 project 不存在：建立並 owner=目前登入 user。
  - 若 project 已存在且 owner 是自己：可覆蓋。
  - 若 project 已存在且 owner 不是自己：會被拒絕。
  - `guest` 不可上傳。

### 6.2 下載（Net -> Desktop）

![vp-download](../img/vp-download.png)

- 下載可不登入，直接輸入：
  - project-id（例如 `VP-RIQMVZ`）
  - 或完整 project URL（例如 `https://visualportfolio.sibuzu.com/projects/VP-RIQMVZ`）
- 也可登入後取得自己的專案列表再點選下載。

## 7. Help 文件入口

- 主頁與專案頁右上角有 Help icon。
- 點擊後會開啟 `/docs`（固定共用同一個 docs 分頁）。

## 8. 系統清理規則

1. 每次服務啟動會先檢查一次。
2. 之後每 1 小時檢查一次。
3. 專案超過 72 小時未 access 會刪除。
4. `user_id=admin` 的專案不會自動清理。

## 9. 常見問題

### Q1. 為什麼我看到「可檢視」但還能改口數/權重？

A：那是本地試算，僅影響當下畫面，不會儲存到 server。

### Q2. 為什麼 Reload 後設定又變回來？

A：因為你在可檢視模式，設定不會寫回 server。

### Q3. 分享連結給別人後，對方可以改壞我的資料嗎？

A：非 owner 只能可檢視，不會覆蓋你的 server 設定；若對方要保存自己的版本，需先複製專案。
