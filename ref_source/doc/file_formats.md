# 檔案格式說明

Visual Portfolio 支援讀取多種回測結果格式，並能儲存/匯出自有的專案與合併交易紀錄。

---

## 支援的回測結果格式

### SRP 格式（`.srp` / `.xml`）

由 TradeStation 或 MultiCharts 等平台輸出的策略回測報表，XML 結構如下：

```xml
<策略回測>
  <參數>
    <最小跳動點>1</最小跳動點>
    <最小跳動金額>200</最小跳動金額>
    <滑價>0</滑價>
  </參數>
  <策略交易>
    <Trade index="1" bs="B" contract="1" price="18000" time_stamp="2023/01/02 09:00:00" symbol="TXFF" />
    <Trade index="1" bs="S" contract="1" price="18200" time_stamp="2023/01/03 13:30:00" symbol="TXFF" />
    <!-- ... -->
  </策略交易>
</策略回測>
```

**重要欄位：**

| 欄位 | 說明 |
|------|------|
| `最小跳動點` | 每一點的單位數量 |
| `最小跳動金額` | 每一點對應的金額；PointValue = 最小跳動金額 / 最小跳動點 |
| `滑價` | 成交滑點，可為點數或百分比格式（如 `2` 或 `0.01%`） |
| `bs` | 買賣方向：`B` = 買入、`S` = 賣出 |
| `contract` | 口數 |
| `price` | 成交價格 |
| `time_stamp` | 成交時間（格式：`yyyy/MM/dd HH:mm:ss`） |
| `symbol` | 商品代碼（可選） |
| `type` | 若值為 `x`，表示每日結算記錄（非實際成交） |

---

### XRP 格式（`.xrp`）

加密貨幣策略專用格式，XML 根節點為 `CryptoReport`：

```xml
<CryptoReport>
  <Trades>
    <Trade bs="B" qty="0.5" amount="-15000" time_stamp="2023/01/02 10:00:00" />
    <Trade bs="S" qty="0.5" amount="16000" time_stamp="2023/01/10 14:00:00" />
    <!-- bs="N" 表示每日結算（虛擬出場/重新進場）-->
    <Trade bs="N" price="15500" time_stamp="2023/01/05 00:00:00" />
  </Trades>
</CryptoReport>
```

**重要欄位：**

| 欄位 | 說明 |
|------|------|
| `bs` | `B`=買入, `S`=賣出, `N`=每日結算（換倉） |
| `qty` | 交易數量（正數） |
| `amount` | 交易金額（買入為負，賣出為正） |
| `price` | 結算價格（僅用於 `bs=N` 的情況） |

---

## 專案檔（`.pfo`）

儲存目前已載入的策略清單與設定，XML 格式如下：

```xml
<?xml version="1.0" encoding="utf-8"?>
<!--Portfolio Trade List-->
<PortfolioyList>
  <Equity Index="1" FileName="C:\data\strategy1.srp" Color="#0000FF" Count="2" Weight="1" 名稱="台指多" />
  <Equity Index="2" FileName="C:\data\strategy2.srp" Color="#FF7F00" Count="1" Weight="1" />
</PortfolioyList>
```

**欄位說明：**

| 屬性 | 說明 |
|------|------|
| `FileName` | 回測結果檔案的完整路徑；若檔案不存在，會自動嘗試與 `.pfo` 同目錄下的同名檔 |
| `Color` | 圖表中的顯示顏色（HTML 色碼） |
| `Count` | 下單口數 |
| `Weight` | 策略權重係數 |
| `名稱` | 自訂策略名稱（選填） |

---

## 匯出格式（`.xml` / `.srp` / `.xrp`）

透過工具列「匯出」功能，可將所有策略的交易記錄合併匯出為 SRP 格式，供其他工具（如再次合入更多策略或用另一個工具分析）使用。

---

## 設定檔（`VisualPortfolio.xml`）

程式啟動目錄下的設定檔，儲存全域選項（關閉時自動寫入）：

```xml
<Setting>
  <MddCount>5</MddCount>
  <Capital>100</Capital>
  <RiskFreeRate>3</RiskFreeRate>
  <計算每日DD>0</計算每日DD>
</Setting>
```

---

## 版面設定檔（`PorfilioPanel.xml`）

程式關閉時自動儲存目前的面板排列位置，下次開啟時自動還原。若此檔不存在，則使用預設版面。

---

*回到 [主說明頁](./README.md)*
