using System;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Windows.Forms;
using VisualPortfolio.Classes;
using WeifenLuo.WinFormsUI.Docking;

namespace VisualPortfolio.Forms
{
    public partial class FormDiversity : DockContent
    {
        private class StrategySnapshot
        {
            public string Name;
            public decimal RawWeight;
            public decimal Amount;
            public int TradeCount;
            public Dictionary<DateTime, double> DailyProfits = new Dictionary<DateTime, double>();
            public double Sigma;
            public double AvgCorrelation;
        }

        private class MetricRow
        {
            public string 項目 { get; set; }
            public string 數值 { get; set; }
            public string 參考 { get; set; }
            public string 說明 { get; set; }
        }

        private class DetailRow
        {
            public string 策略 { get; set; }
            public string 成交占比 { get; set; }
            public string 交易次數 { get; set; }
            public string 總交易金額 { get; set; }
            public string 平均交易金額 { get; set; }
            public string 平均相關性 { get; set; }
        }

        public FormDiversity()
        {
            InitializeComponent();
        }

        internal void UpdateDiversityTable()
        {
            var snapshots = BuildSnapshots();
            var metrics = BuildMetricRows(snapshots);
            var details = BuildDetailRows(snapshots);

            dvSummary.DataSource = metrics;
            dvDetail.DataSource = details;

            ApplyGridStyle(dvSummary);
            ApplyGridStyle(dvDetail);
        }

        private void ApplyGridStyle(DataGridView grid)
        {
            if (grid.Columns.Count == 0)
            {
                return;
            }

            grid.AutoResizeColumns();
            foreach (DataGridViewColumn column in grid.Columns)
            {
                column.SortMode = DataGridViewColumnSortMode.NotSortable;
            }
        }

        private List<StrategySnapshot> BuildSnapshots()
        {
            var results = new List<StrategySnapshot>();
            DateTime dtStart = Global.frmEquityManage.GetRangeStart().Date;
            DateTime dtEnd = Global.frmEquityManage.GetRangeEnd().Date.AddDays(1).AddSeconds(-1);

            foreach (var equity in Global.listEquityAttr)
            {
                if (!equity.Active)
                {
                    continue;
                }

                var snapshot = new StrategySnapshot
                {
                    Name = equity.GetName(),
                    RawWeight = Math.Abs(equity.Contract * equity.Weight)
                };

                foreach (var item in equity.TradeList.Items)
                {
                    if (item.tradeDate2 < dtStart)
                    {
                        continue;
                    }
                    if (item.tradeDate2 > dtEnd)
                    {
                        break;
                    }

                    snapshot.TradeCount++;
                    snapshot.Amount += Math.Abs(item.tradeAmount * equity.Contract * equity.Weight);

                    DateTime key = item.tradeDate2.Date;
                    double profit = (double)(item.netProfit * equity.Contract * equity.Weight);
                    if (snapshot.DailyProfits.ContainsKey(key))
                    {
                        snapshot.DailyProfits[key] += profit;
                    }
                    else
                    {
                        snapshot.DailyProfits[key] = profit;
                    }
                }

                if (snapshot.TradeCount == 0 && snapshot.Amount == 0)
                {
                    continue;
                }

                snapshot.Sigma = CalcStdDev(snapshot.DailyProfits.Values);
                results.Add(snapshot);
            }

            if (results.Count == 0)
            {
                return results;
            }

            double[,] corr = BuildCorrelationMatrix(results);
            for (int i = 0; i < results.Count; ++i)
            {
                if (results.Count == 1)
                {
                    results[i].AvgCorrelation = 1.0;
                    continue;
                }

                double sum = 0;
                for (int j = 0; j < results.Count; ++j)
                {
                    if (i == j)
                    {
                        continue;
                    }
                    sum += corr[i, j];
                }
                results[i].AvgCorrelation = sum / (results.Count - 1);
            }

            return results;
        }

        private List<MetricRow> BuildMetricRows(List<StrategySnapshot> snapshots)
        {
            var rows = new List<MetricRow>();
            int stratCount = snapshots.Count;

            if (stratCount == 0)
            {
                rows.Add(new MetricRow
                {
                    項目 = "沒有可計算資料",
                    數值 = "-",
                    參考 = "-",
                    說明 = "目前日期區間內沒有啟用策略交易。"
                });
                return rows;
            }

            // -------------------------------------------------------
            // 1. Build merged trade list from all active strategies.
            //    Trades at the same timestamp are collapsed into one
            //    entry (amounts summed) so N counts distinct time-slots.
            // -------------------------------------------------------
            // perStratByTime[timestamp][strategyIndex] = weighted amount
            var mergedByTime      = new SortedDictionary<DateTime, double>();
            var perStratByTime    = new SortedDictionary<DateTime, double[]>();
            DateTime dtStart = Global.frmEquityManage.GetRangeStart().Date;
            DateTime dtEnd   = Global.frmEquityManage.GetRangeEnd().Date.AddDays(1).AddSeconds(-1);

            for (int si = 0; si < snapshots.Count; si++)
            {
                var equity = Global.listEquityAttr.FirstOrDefault(e => e.Active && e.GetName() == snapshots[si].Name);
                if (equity == null) continue;
                foreach (var item in equity.TradeList.Items)
                {
                    if (item.tradeDate2 < dtStart) continue;
                    if (item.tradeDate2 > dtEnd)   break;

                    double amt = Math.Abs((double)item.tradeAmount * (double)equity.Contract * (double)equity.Weight);
                    DateTime key = item.tradeDate2;

                    if (!mergedByTime.ContainsKey(key))
                    {
                        mergedByTime[key]   = 0;
                        perStratByTime[key] = new double[snapshots.Count];
                    }
                    mergedByTime[key]        += amt;
                    perStratByTime[key][si]  += amt;
                }
            }

            // N = number of distinct time-slots (merged trades)
            int    N           = mergedByTime.Count;
            double totalAmount = mergedByTime.Values.Sum();
            double avgAmount   = N == 0 ? 0 : totalAmount / N;

            // HHI and N_eff on merged per-trade amounts
            double hhi  = 0;
            if (totalAmount > 0)
            {
                foreach (var amt in mergedByTime.Values)
                {
                    double share = amt / totalAmount;
                    hhi += share * share;
                }
            }
            double nEff = hhi == 0 ? 0 : 1.0 / hhi;
            double eer  = N  == 0 ? 0 : nEff / N;

            // -------------------------------------------------------
            // 2. Strategy-level metrics (RDR, DCI, ENB) – unchanged
            // -------------------------------------------------------
            double totalWeight     = snapshots.Sum(x => (double)x.RawWeight);
            double[] strategyWeights = snapshots.Select(x => totalWeight == 0 ? 0 : (double)x.RawWeight / totalWeight).ToArray();

            double[] portfolioSeries = BuildPortfolioSeries(snapshots);
            double sigmaP = CalcStdDev(portfolioSeries);
            // Each snapshot.Sigma is already dollar-scaled (profits include Contract×Weight),
            // so the numerator Σ(w_i·σ_i) must also be in dollar scale.
            // Use raw sigma sum (equivalent to w_i = 1 per strategy in dollar terms).
            double sigmaWeighted = snapshots.Sum(s => s.Sigma);
            double rdr = sigmaP == 0 ? 0 : sigmaWeighted / sigmaP;

            double[,] corr = BuildCorrelationMatrix(snapshots);
            double dciNumerator   = 0;
            double dciDenominator = 0;
            double enbDenominator = 0;
            for (int i = 0; i < snapshots.Count; ++i)
            {
                enbDenominator += strategyWeights[i] * strategyWeights[i];
                for (int j = 0; j < snapshots.Count; ++j)
                {
                    if (i != j)
                    {
                        double pairWeight  = strategyWeights[i] * strategyWeights[j];
                        dciNumerator      += pairWeight * corr[i, j];
                        dciDenominator    += pairWeight;
                    }
                    enbDenominator += (i == j) ? 0 : strategyWeights[i] * strategyWeights[j] * corr[i, j];
                }
            }
            double dci = dciDenominator == 0 ? 1.0 : dciNumerator / dciDenominator;
            double isn = enbDenominator <= 0 ? 0 : 1.0 / enbDenominator;

            // -------------------------------------------------------
            // 3. DSN: Distributed Strategy Number
            //    For each time-slot t:
            //      DSN_t = n · Σ_i (w_i,t)² / (Σ_i w_i,t)²
            //    where n = strategy count, w_i,t = weighted amount (0 if not trading).
            //    Range: [1, n] — 1 means fully dispersed (equal weights), n means fully concentrated.
            //    Overall DSN = weighted average of DSN_t (weight = total amount at t).
            // -------------------------------------------------------
            double dsn = 0;
            if (stratCount >= 2 && totalAmount > 0)
            {
                double dsnWeightedSum = 0;
                double dsnTotalWeight = 0;

                foreach (var kvp in perStratByTime)
                {
                    double[] w = kvp.Value;          // length == stratCount

                    double sumW  = 0;
                    double sumW2 = 0;
                    foreach (double wi in w)
                    {
                        sumW  += wi;
                        sumW2 += wi * wi;
                    }

                    if (sumW <= 0) continue;         // all-zero slot (shouldn't happen)

                    double dsnT = (double)stratCount * sumW2 / (sumW * sumW);  // concentration index
                    dsnWeightedSum += dsnT * sumW;   // weight by total amount at this slot
                    dsnTotalWeight += sumW;
                }

                dsn = dsnTotalWeight > 0 ? dsnWeightedSum / dsnTotalWeight : 0;
            }

            // -------------------------------------------------------
            // 3. Emit rows
            // -------------------------------------------------------
            rows.Add(new MetricRow { 項目 = "總策略數",            數值 = stratCount.ToString(),       參考 = "任意整數",       說明 = "參與分析的啟用策略數量。" });
            rows.Add(new MetricRow { 項目 = "總交易次數 (N)",        數值 = N.ToString("#,##0"),         參考 = "任意整數",       說明 = "合併後不同時間點的總交易次數（同一時刻算一次）。" });
            rows.Add(new MetricRow { 項目 = "平均每次交易金額",      數值 = avgAmount.ToString("#,##0"),  參考 = "任意正實數",   說明 = "總成交金額 ÷ 總交易次數。" });
            rows.Add(new MetricRow { 項目 = "有效交易次數 (N_eff)",  數值 = nEff.ToString("#,##0"),       參考 = "1 ~ N",         說明 = "1/HHI，越大越分散。" });
            rows.Add(new MetricRow { 項目 = "進場效率比 (EER)",      數值 = eer.ToString("0.00%"),        參考 = "0% ~ 100%",     說明 = "N_eff / N，越接近 100% 表示交易金額分布越均匀。" });
            rows.Add(new MetricRow { 項目 = "風險分散率 (RDR)",      數值 = rdr.ToString("0.00"),        參考 = ">= 1.0",       說明 = "(標準差) 組合的標準差與原標準相比。愈大表示變異愈大。" });
            rows.Add(new MetricRow { 項目 = "分散相關指數 (DCI)",  數值 = dci.ToString("0.00%"),        參考 = "-100% ~ 100%", 說明 = "(相關係數) 越低越分散，負值代表策略彼此有對沖效果。" });
            rows.Add(new MetricRow { 項目 = "獨立策略數 (ISN)",      數值 = isn.ToString("0.00"),        參考 = "1 ~ 策略數",   說明 = "(績效獨立策略數) 同時考慮權重與相關性的有效獨立策略數。" });
            rows.Add(new MetricRow { 項目 = "分散策略數 (DSN)",      數值 = dsn.ToString("0.00"),        參考 = "1 ~ 策略數",   說明 = "(進場獨立策略數) 等效完全分散的策略數，n 代表完全不重疊，1 代表完全同步進場。" });

            return rows;
        }

        private List<DetailRow> BuildDetailRows(List<StrategySnapshot> snapshots)
        {
            var rows = new List<DetailRow>();
            decimal totalAmount = snapshots.Sum(x => x.Amount);

            foreach (var snapshot in snapshots.OrderByDescending(x => x.Amount))
            {
                rows.Add(new DetailRow
                {
                    策略 = snapshot.Name,
                    成交占比 = totalAmount == 0 ? "0.00%" : ((double)(snapshot.Amount / totalAmount)).ToString("0.00%"),
                    交易次數 = snapshot.TradeCount.ToString("#,##0"),
                    總交易金額 = snapshot.Amount.ToString("#,##0"),
                    平均交易金額 = snapshot.TradeCount == 0 ? "0" : (snapshot.Amount / snapshot.TradeCount).ToString("#,##0"),
                    平均相關性 = snapshot.AvgCorrelation.ToString("0.00%")
                });
            }

            return rows;
        }

        private double[] BuildPortfolioSeries(List<StrategySnapshot> snapshots)
        {
            var dates = new SortedSet<DateTime>();
            foreach (var snapshot in snapshots)
            {
                foreach (var date in snapshot.DailyProfits.Keys)
                {
                    dates.Add(date);
                }
            }

            var values = new List<double>();
            foreach (var date in dates)
            {
                double sum = 0;
                foreach (var snapshot in snapshots)
                {
                    double value;
                    if (snapshot.DailyProfits.TryGetValue(date, out value))
                    {
                        sum += value;
                    }
                }
                values.Add(sum);
            }
            return values.ToArray();
        }

        private double[,] BuildCorrelationMatrix(List<StrategySnapshot> snapshots)
        {
            int n = snapshots.Count;
            var matrix = new double[n, n];
            var dates = new SortedSet<DateTime>();
            foreach (var snapshot in snapshots)
            {
                foreach (var date in snapshot.DailyProfits.Keys)
                {
                    dates.Add(date);
                }
            }

            var orderedDates = dates.ToList();
            var series = snapshots
                .Select(snapshot => orderedDates.Select(date => snapshot.DailyProfits.ContainsKey(date) ? snapshot.DailyProfits[date] : 0).ToArray())
                .ToArray();

            for (int i = 0; i < n; ++i)
            {
                for (int j = i; j < n; ++j)
                {
                    double value = i == j ? 1.0 : CalcCorrelation(series[i], series[j]);
                    matrix[i, j] = value;
                    matrix[j, i] = value;
                }
            }

            return matrix;
        }

        private double CalcStdDev(IEnumerable<double> values)
        {
            var list = values.ToList();
            if (list.Count == 0)
            {
                return 0;
            }

            double mean = list.Average();
            double variance = list.Sum(x => (x - mean) * (x - mean)) / list.Count;
            return Math.Sqrt(variance);
        }

        private double CalcCorrelation(double[] x, double[] y)
        {
            if (x.Length == 0 || y.Length == 0 || x.Length != y.Length)
            {
                return 0;
            }

            double meanX = x.Average();
            double meanY = y.Average();
            double sumXY = 0;
            double sumXX = 0;
            double sumYY = 0;

            for (int i = 0; i < x.Length; ++i)
            {
                double dx = x[i] - meanX;
                double dy = y[i] - meanY;
                sumXY += dx * dy;
                sumXX += dx * dx;
                sumYY += dy * dy;
            }

            if (sumXX == 0 || sumYY == 0)
            {
                return 0;
            }

            double value = sumXY / Math.Sqrt(sumXX * sumYY);
            if (value > 1) return 1;
            if (value < -1) return -1;
            return value;
        }

        private void btnRefresh_Click(object sender, EventArgs e)
        {
            UpdateDiversityTable();
        }

        private void btnHelp_Click(object sender, EventArgs e)
        {
            System.Diagnostics.Process.Start("https://github.com/sibuzu/mydoc/blob/main/%E5%A4%9A%E6%A8%A3%E6%80%A7%E5%88%86%E6%9E%90%E6%8C%87%E6%A8%99.md");
        }

        private void mtnSaveSummary_Click(object sender, EventArgs e)
        {
            SaveGrid(dvSummary, "Diversity Summary|*.csv|All Files|*.*");
        }

        private void mtnSaveDetail_Click(object sender, EventArgs e)
        {
            SaveGrid(dvDetail, "Diversity Detail|*.csv|All Files|*.*");
        }

        private void SaveGrid(DataGridView grid, string filter)
        {
            var dlg = new SaveFileDialog();
            dlg.Filter = filter;
            dlg.FilterIndex = 1;

            if (dlg.ShowDialog() == DialogResult.OK)
            {
                util.ExportTable(dlg.FileName, grid);
            }
        }
    }
}
