VisualPortfolio.Net Spec Requirement

1. 專案在建立 VisualPortfolio.Net，可以用網頁給用戶使用，已經有 C# WinForm 版本，在 ref_source/ 下。依據 ref_source/，寫出相同功能的網頁版。

2. 前端展示層 (Frontend): 使用 Vue.js + EChart，可上傳 srp, xrp (都是 xml 格式)，參考files 可以看 ref_result/project

3. 端處理層 (Backend): 負責邏輯計算、檔案解析與 API 管理。使用 Python + FastAPI。

4. 資料儲存層 (Database & Storage): 使用 Sqlite db (data/db/ 目錄下), 有一個 project db 其 columns:
   project-id, user-id, project-name, create-time, access-time

5. **分配訪客 ID：** 當使用者第一次進入網頁，後端或前端產生一個隨機的 **Guest_UUID** (550e8400-e29b-41d4...)。

   **存入瀏覽器：** 將這個 UUID 存入 LocalStorage。

   **建立新專案：** 建立專案時，需打入專案名稱，將這個 `Guest_UUID` 寫入資料庫的 `user-id` 欄位，並產生一個的 project-id (例如：VPGE-DEFK  -> VP[A-Z]{2}-[A-Z]{4} )。

   **讀取記錄：** 當使用者再次回到網頁，前端從 LocalStorage 讀出 UUID，並向後端請求：`GET /projects?guest_id=...`。

6. user_id 相等 -> 可編輯
   user_id 不相等 -> 可觀看(唯讀)

7. 建立project dir = data/projects/{project-id}，之前上傳的 srp xrp files 或是 建立的 pfo 都是放在這個project dir

8. 每次project access (edit/view) 都會更 db 的 project access time。若是72小時都沒access 的 project，則會刪除。

9. Dynamic Compounding 的「回徹金額」參數需同時支援「萬」與「%」兩種輸入模式：
   - 無 `%` 後綴時，視為萬（例如 `2000` = 2000萬）
   - 有 `%` 後綴時，視為從高點回撤比例（例如 `10%` = 從高點損失 10% 觸發回切）
