## Why

目前專案只有正式站流程，缺少一個可長期存在、可獨立驗證的 beta 環境，導致新功能或修正難以先在真實部署條件下驗證。現在需要先建立 beta 站並隔離資料與部署資源，讓變更可先測試通過再推到正式站。

## What Changes

- 新增 beta 網站部署能力，提供 `visualporforlio-beta.sibuzu.com` 作為預發布驗證入口。
- 建立與正式環境隔離的 beta 執行配置，使用 `data-beta` 作為資料目錄。
- 新增 beta 專用 docker 配置（以 `docker/visual-portfolio-beta` 為基礎路徑），避免與正式部署互相影響。
- 定義 beta 驗證流程要求：功能需與正式站一致，通過 beta 測試後才可上線到正式站。

## Capabilities

### New Capabilities
- `beta-environment-deployment`: 建立 beta 子網域、獨立資料目錄與獨立 docker 部署配置，支援上線前驗證。

### Modified Capabilities
- （無）

## Impact

- Affected systems: DNS / reverse proxy / deployment scripts / docker compose and runtime configuration。
- Affected paths: `docker/` 下新增或調整 beta 配置、資料路徑設定（`data-beta`）。
- Operational impact: release 流程需新增 beta 驗證關卡。
