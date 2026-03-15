using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Xml;
using VisualPortfolio.Classes;

namespace VisualPortfolio
{
    internal class ClsMDD
    {
        internal double Value;
        internal int StartIdx;
        internal int EndIdx;
        internal int EndIdx2;
    }

    public class TSummaryReport
    {
        internal List<ClsMDD> listMDD;
        private List<TReportEntry>[] _reportList;
        private List<TReportEntry> _reportParamters;
        private List<TReportEntry> _annaulProfit;
        private List<TReportEntry> _monthProfit;
        private List<TReportEntry> _weekProfit;
        private List<TReportEntry> _dailyProfit;

        public TSummaryReport()
        {
            int n = 14;
            _reportList = new List<TReportEntry>[n];
            for (int i = 0; i < n; ++i)
                _reportList[i] = new List<TReportEntry>();
            _reportParamters = new List<TReportEntry>();
            _annaulProfit = new List<TReportEntry>();
            _monthProfit = new List<TReportEntry>();
            _weekProfit = new List<TReportEntry>();
            _dailyProfit = new List<TReportEntry>();

            this.MddCount = 5;
        }

        public string Symbol { get; set; }
        public string Strategy { get; set; }
        public string TradeTime { get; set; }
        public double TradePeriod { get; set; }
        public bool SimulatedTick { get; set; }
        public int MddCount { get; set; }

        public List<TReportEntry> GetReportList(int idx)
        {
            return _reportList[idx];
        }

        public List<TReportEntry> GetAnnualReport()
        {
            return _annaulProfit;
        }

        public List<TReportEntry> GetMonthReport()
        {
            return _monthProfit;
        }

        public List<TReportEntry> GetWeekReport()
        {
            return _weekProfit;
        }

        public List<TReportEntry> GetDailyReport()
        {
            return _dailyProfit;
        }

        public List<TReportEntry> ReportParamters
        {
            get { return _reportParamters; }
        }

        private void AddReportEntry(int idx, string name, string value)
        {
            _reportList[idx].Add(new TReportEntry(name, value));
        }

        private void CreateSummaryPart(List<ClsTradeItem> lp, double factor)
        {
            double NetProfit = 0;
            int TotalTrade = lp.Count;
            int WinTrade = 0;
            int LossTrade = 0;
            double MaxDrawDownPrice = 0;
            double DrawDown = 0;
            double ProfitFactor = 0;
            double AvgNetProfit = 0;
            double AvgWinProfit = 0;
            double AvgLossProfit = 0;
            double AvgWinLossRatio = 0;
            double WinProfit = 0;
            double LossProfit = 0;
            double WinProb = 0;
            double Profit2 = 0;
            double Sqn = 0;
            double SharpeRatio = 0;
            double SortinoRatio = 0;
            int MDD_Start_Candidate = 0;
            listMDD = new List<ClsMDD>();
            ClsMDD curMDD = new ClsMDD();

            // Set Report List
            int idx0 = Global.IDX_SUMMARY0;
            int idx1 = Global.IDX_SUMMARY1;
            _reportList[idx0].Clear();
            _reportList[idx1].Clear();

            if (lp.Count == 0) return;

            for (int i = 0; i < lp.Count; ++i)
            {
                ClsTradeItem pr = lp[i];
                double profit = (double)pr.netProfit * (double)pr.aux_count * (double)pr.aux_weight * factor;
                NetProfit += profit;
                Profit2 += profit * profit;
                if (pr.netProfit > 0)
                {
                    WinTrade++;
                    WinProfit += profit;
                }
                else
                {
                    LossTrade++;
                    LossProfit += profit;
                }

                DrawDown += profit;
                if (DrawDown >= 0)
                {
                    DrawDown = 0;
                    MDD_Start_Candidate = i;
                    if (curMDD.Value < 0)
                    {
                        curMDD.EndIdx2 = i - 1;
                        listMDD.Add(curMDD);
                        curMDD = new ClsMDD();
                    }
                }
                if (DrawDown < curMDD.Value)
                {
                    curMDD.Value = DrawDown;
                    curMDD.StartIdx = MDD_Start_Candidate;
                    curMDD.EndIdx = i;
                }
            }
            if (curMDD.Value < 0)
            {
                curMDD.EndIdx2 = lp.Count - 1;
                listMDD.Add(curMDD);
                curMDD = new ClsMDD();
            }
            listMDD = listMDD.OrderBy(o => o.Value).ToList();

            AvgNetProfit = (TotalTrade == 0) ? 0 : NetProfit / TotalTrade;
            ProfitFactor = (LossProfit == 0) ? 100 : (-WinProfit / LossProfit);

            WinProb = ((WinTrade == 0) ? 0 : WinTrade * 100.0 / TotalTrade);
            AvgWinProfit = (WinTrade == 0) ? 0 : WinProfit / WinTrade;
            AvgLossProfit = (LossTrade == 0) ? 0 : LossProfit / LossTrade;
            AvgWinLossRatio = (AvgLossProfit == 0) ? 0 : -AvgWinProfit / AvgLossProfit;

            /* 
             * SQN or SystemQualityNumber. Defined by Van K. Tharp to categorize trading systems.
                - 1.6 - 1.9 Below average
                - 2.0 - 2.4 Average
                - 2.5 - 2.9 Good
                - 3.0 - 5.0 Excellent
                - 5.1 - 6.9 Superb
                - 7.0 - Holy Grail?

             The formula:
                - SquareRoot(NumberTrades) * Average(TradesProfit) / StdDev(TradesProfit)
                  The sqn value should be deemed reliable when the number of trades >= 30
            */

            if (TotalTrade > 0)
            {
                double stddev = Math.Sqrt((double)(Profit2 / TotalTrade - AvgNetProfit * AvgNetProfit));
                Sqn = Math.Sqrt((double)TotalTrade) * (double)AvgNetProfit / stddev;
            }

            // period
            DateTime t1 = lp[0].tradeDate2;
            DateTime t2 = lp[lp.Count - 1].tradeDate2;
            this.TradePeriod = (t2 - t1).Days;
            double yr = ((t2 - t1).Days + 1) / 365.25;
            string period1 = string.Format("{0:0.00} years", yr);
            string period2 = string.Format("{0:yyyy/MM/dd} - {1:yyyy/MM/dd}", t1, t2);

            if (yr == 0) return;

            if (TotalTrade > 0 && Global.Capital > 0)
            {
                // Calc Shape Ratio
                List<double> ep = new List<double>();
                DateTime lastDate = DateTime.MinValue;
                for (int i = 0; i < lp.Count; ++i)
                {
                    ClsTradeItem pr = lp[i];
                    if (pr.tradeDate2.Date != lastDate)
                    {
                        ep.Add(0);
                        lastDate = pr.tradeDate2.Date;
                    }
                    double profit = (double)pr.netProfit * (double)pr.aux_count * (double)pr.aux_weight * factor;
                    ep[ep.Count-1] += profit;
                }

                double N = ep.Count / yr;
                double rf = Global.RiskFreeRate * 0.01 / N;
                double capital = Global.Capital * 10000;
                ep = ep.Select(x => (x / capital - rf)).ToList();
                SharpeRatio = CalcShapeRatio(ep, N);
                SortinoRatio = CalcSortinoRatio(ep, N);
            }

            double YrProfit = NetProfit / yr;
            double MDD = (listMDD.Count > 0) ? -listMDD[0].Value : 0;
            double PMR = (MDD == 0) ? 0 : NetProfit / MDD;
            double YPMR = (MDD == 0) ? 0 : YrProfit / MDD;
            Global.TotalMDD = (decimal) MDD;

            string fmt1 = "#,##0";
            string fmt2 = "#,##0.##";
            AddReportEntry(idx0, "期間", period1);
            AddReportEntry(idx0, "總獲利", "$ " + NetProfit.ToString(fmt1));
            AddReportEntry(idx0, "年獲利", "$ " + (NetProfit / yr).ToString(fmt1));
            AddReportEntry(idx0, "MDD", "$ " + MDD.ToString(fmt1));
            AddReportEntry(idx0, "總獲利/MDD", PMR.ToString(fmt2));
            AddReportEntry(idx0, "年獲利/MDD", YPMR.ToString(fmt2));
            AddReportEntry(idx0, "贏錢總金額", "$ " + WinProfit.ToString(fmt1));
            AddReportEntry(idx0, "輸錢總金額", "$ " + LossProfit.ToString(fmt1));
            AddReportEntry(idx0, "獲利因子", ProfitFactor.ToString(fmt2));
            AddReportEntry(idx0, "Sortino Ratio", SortinoRatio.ToString(fmt2));
            // AddReportEntry(idx0, "Sharpe Ratio", SharpeRatio.ToString(fmt2));

            AddReportEntry(idx1, "交易日期", period2);
            AddReportEntry(idx1, "交易次數", TotalTrade.ToString(fmt1));
            AddReportEntry(idx1, "贏錢次數", WinTrade.ToString(fmt1));
            AddReportEntry(idx1, "輸錢次數", LossTrade.ToString(fmt1));
            AddReportEntry(idx1, "贏錢機率", WinProb.ToString(fmt2) + "%");
            AddReportEntry(idx1, "平均每次輸贏", "$ " + AvgNetProfit.ToString(fmt1));
            AddReportEntry(idx1, "平均每次贏錢", "$ " + AvgWinProfit.ToString(fmt1));
            AddReportEntry(idx1, "平均每次輸錢", "$ " + AvgLossProfit.ToString(fmt1));
            // AddReportEntry(idx1, "SQN", Sqn.ToString(fmt2));
            AddReportEntry(idx1, "Sharpe Ratio", SharpeRatio.ToString(fmt2));
            AddReportEntry(idx1, "", "");

            for (int i = 0; i < MddCount && i < listMDD.Count; ++i)
            {
                MaxDrawDownPrice = -listMDD[i].Value;
                string mdd = string.Format("$ {0:#,##0.##}", MaxDrawDownPrice);
                if (MaxDrawDownPrice > 0)
                {
                    TimeSpan ts1 = lp[listMDD[i].EndIdx].tradeDate2 - lp[listMDD[i].StartIdx].tradeDate2;
                    TimeSpan ts2 = lp[listMDD[i].EndIdx2].tradeDate2 - lp[listMDD[i].StartIdx].tradeDate2;
                    mdd += string.Format("  ({0:yyyy/MM/dd}, {1} - {2} days)",
                        lp[listMDD[i].StartIdx].tradeDate2, (int)ts1.TotalDays, (int)ts2.TotalDays);
                }
                AddReportEntry((i + 0) % 2, "MDD " + (i + 1).ToString(), mdd);
            }
        }

        private double CalcShapeRatio(List<double> ep, double n)
        {
            double mean = ep.Average();
            double std = Math.Sqrt(ep.Select(x => Math.Pow(x - mean, 2)).Average());
            if (std == 0) return 0;
            double sharpe = Math.Sqrt(n) * mean / std;
            return sharpe;
        }

        private double CalcSortinoRatio(List<double> ep, double n)
        {
            double mean = ep.Average();
            var downsideReturns = ep.Where(x => x < 0).ToList();
            if (downsideReturns.Count == 0) return 0;
            double std = Math.Sqrt(downsideReturns.Select(x => Math.Pow(x, 2)).Average());
            if (std == 0) return 0;
            double sortino = Math.Sqrt(n) * mean / std;
            return sortino;
        }

        public static int GetYearMonth(DateTime dt, int mi)
        {
            int year = dt.Year;
            int month = dt.Month - 1;
            return year * 100 + (month / mi) * mi + 1;
        }

        public static void CalcYearMonthProfit(List<ClsTradeItem> lp, double factor,
            int minterval,
            List<int> years, List<int> months,
            List<double> yearProfits, List<double> monthProfits,
            List<double> yearMDD, List<double> monthMDD)
        {
            int curYear = 0;
            int curMonth = 0;

            DateTimeFormatInfo dfi = DateTimeFormatInfo.CurrentInfo;
            Calendar cal = dfi.Calendar;
            double yearDD = 0;
            double monthDD = 0;
            int ym;

            foreach (ClsTradeItem pr in lp)
            {
                double profit = (double)pr.netProfit * (double)pr.aux_count * (double)pr.aux_weight * factor;
                ym = GetYearMonth(pr.tradeDate2, minterval);
                if (ym == curYear)
                {
                    yearProfits[yearProfits.Count - 1] += profit;
                    yearDD -= profit;
                    if (yearDD < 0) yearDD = 0;
                    if (yearDD > yearMDD[yearMDD.Count - 1])
                    {
                        yearMDD[yearMDD.Count - 1] = yearDD;
                    }
                }
                else
                {
                    // new item
                    curYear = ym;
                    years.Add(curYear);
                    yearProfits.Add(profit);
                    yearDD = -profit;
                    if (yearDD < 0) yearDD = 0;
                    yearMDD.Add(yearDD);
                }

                ym = GetYearMonth(pr.tradeDate2, 1);
                if (ym == curMonth)
                {
                    monthProfits[monthProfits.Count - 1] += profit;
                    monthDD -= profit;
                    if (monthDD < 0) monthDD = 0;
                    if (monthDD > monthMDD[monthMDD.Count - 1])
                    {
                        monthMDD[monthMDD.Count - 1] = monthDD;
                    }
                }
                else
                {
                    // new item
                    curMonth = ym;
                    months.Add(curMonth);
                    monthProfits.Add(profit);
                    monthDD = -profit;
                    if (monthDD < 0) monthDD = 0;
                    monthMDD.Add(monthDD);
                }
            }
        }

        private void CreaeteAnnualPart(List<ClsTradeItem> lp, double factor)
        {
            List<int> years = new List<int>();
            List<int> months = new List<int>();
            List<double> yearProfits = new List<double>();
            List<double> monthProfits = new List<double>();
            List<double> yearMDD = new List<double>();
            List<double> monthMDD = new List<double>();

            CalcYearMonthProfit(lp, factor, 12, years, months, yearProfits, monthProfits, yearMDD, monthMDD);

            // Set Report List
            int idx0 = Global.IDX_YEAR_PROFIT0;
            int idx1 = Global.IDX_YEAR_PROFIT1;
            int idx2 = Global.IDX_MONTH_PROFIT0;
            int idx3 = Global.IDX_MONTH_PROFIT1;
            int idx4 = Global.IDX_WEEK_PROFIT0;
            int idx5 = Global.IDX_WEEK_PROFIT1;
            _reportList[idx0].Clear();
            _reportList[idx1].Clear();
            _reportList[idx2].Clear();
            _reportList[idx3].Clear();
            _reportList[idx4].Clear();
            _reportList[idx5].Clear();

            int curWeek = -1;
            List<int> weeks = new List<int>();
            List<decimal> weekProfits = new List<decimal>();
            DateTimeFormatInfo dfi = DateTimeFormatInfo.CurrentInfo;
            Calendar cal = dfi.Calendar;

            foreach (var pr in lp)
            {
                double profit = (double)pr.netProfit * (double)pr.aux_count * (double)pr.aux_weight * factor;

                int week = cal.GetWeekOfYear(pr.tradeDate2, dfi.CalendarWeekRule, dfi.FirstDayOfWeek);
                int day = pr.tradeDate2.Day + pr.tradeDate2.Month * 100 + pr.tradeDate2.Year * 10000;
                int weekday = (int)pr.tradeDate2.DayOfWeek;
                if (week == curWeek)
                {
                    // weeks[weeks.Count - 1] = day;
                    weekProfits[weekProfits.Count - 1] += pr.profit;
                }
                else
                {
                    curWeek = week;
                    weeks.Add(day - weekday);
                    weekProfits.Add(pr.profit);
                }
            }

            string fmt = "#,##0";
            for (int i = 0; i < years.Count; i++)
            {
                string yr = (years[i] / 100).ToString();
                AddReportEntry(idx0, yr, yearProfits[i].ToString(fmt));
                AddReportEntry(idx1, yr, yearMDD[i].ToString(fmt));
                AddProfitEntry(_annaulProfit, yr, yearProfits[i], yearMDD[i]);
            }

            string mstr;
            for (int i = 0; i < months.Count; i++)
            {
                mstr = string.Format("{0}/{1:00}", months[i] / 100, months[i] % 100);
                AddReportEntry(idx2, mstr, monthProfits[i].ToString(fmt));
                AddReportEntry(idx3, mstr, monthMDD[i].ToString(fmt));
                AddProfitEntry(_monthProfit, mstr, monthProfits[i], monthMDD[i]);
            }

            decimal total_profit = 0;
            for (int i = 0; i < weeks.Count; i++)
            {
                total_profit += weekProfits[i];
                mstr = string.Format("{0}/{1:00}/{2:00}", weeks[i] / 10000, (weeks[i] / 100) % 100, weeks[i] % 100);
                AddReportEntry(idx4, mstr, weekProfits[i].ToString(fmt));
                AddReportEntry(idx5, mstr, total_profit.ToString(fmt));
            }
        }

        private void AddProfitEntry(List<TReportEntry> listProfit, string name,
            double profit, double mdd, int pos = 9999)
        {
            string fmt = "#,##0.##";
            string p = (pos == 9999) ? "" : pos.ToString();
            listProfit.Add(new TReportEntry(name, profit.ToString(fmt), mdd.ToString(fmt), p));
        }

        public void CreateSimpleReport(List<ClsTradeItem> lp, double factor)
        {
            CreateSummaryPart(lp, factor);
            CreaeteAnnualPart(lp, factor);
        }

        public static void ExportMergeTrade(string filename, List<ClsTradeItem> lp)
        {
            if (lp.Count == 0) return;

            XmlTextWriter xmlOut = new XmlTextWriter(filename, Encoding.UTF8);

            // Use indenting for readability
            xmlOut.Formatting = Formatting.Indented;
            xmlOut.WriteStartDocument();

            // Write first element
            xmlOut.WriteStartElement("策略回測");

            xmlOut.WriteStartElement("參數");
            xmlOut.WriteElementString("策略", "Portfilio");
            xmlOut.WriteElementString("開始日期", lp[0].tradeDate2.ToString("yyyy/MM/dd"));
            xmlOut.WriteElementString("結束日期", lp[lp.Count - 1].tradeDate2.ToString("yyyy/MM/dd"));
            xmlOut.WriteElementString("最小跳動點", "1");
            xmlOut.WriteElementString("最小跳動金額", "1");
            xmlOut.WriteEndElement();

            xmlOut.WriteStartElement("策略交易");
            for (int i = 0; i < lp.Count; i++)
            {
                WriteXml(xmlOut, i + 1, lp[i]);
            }
            xmlOut.WriteEndElement();

            xmlOut.WriteEndElement();

            xmlOut.WriteEndDocument();
            xmlOut.Close();
        }

        private static void WriteXml(XmlTextWriter writer, int i, ClsTradeItem te)
        {
            decimal price2 = te.price2 * te.pointValue;
            decimal price1 = price2 + te.netProfit * (te.buy ? 1 : -1);

            writer.WriteStartElement("Trade");
            writer.WriteAttributeString("index", te.trade_idx.ToString());
            writer.WriteAttributeString("bs", te.buy ? "S" : "B");
            writer.WriteAttributeString("contract", te.aux_count.ToString());
            writer.WriteAttributeString("price", (price1 * te.aux_weight).ToString());
            writer.WriteAttributeString("time_stamp", te.tradeDate1.ToString("yyyy/MM/dd HH:mm:ss"));
            writer.WriteAttributeString("tag", te.tag.ToString());
            writer.WriteEndElement();

            writer.WriteStartElement("Trade");
            writer.WriteAttributeString("index", te.trade_idx.ToString());
            writer.WriteAttributeString("bs", te.buy ? "B" : "S");
            writer.WriteAttributeString("contract", te.aux_count.ToString());
            writer.WriteAttributeString("price", (price2 * te.aux_weight).ToString());
            writer.WriteAttributeString("time_stamp", te.tradeDate2.ToString("yyyy/MM/dd HH:mm:ss"));
            writer.WriteAttributeString("tag", te.tag.ToString());
            writer.WriteEndElement();
        }
    }

    public class TDetailEntry
    {
        public string index, strategy, date, trade, price, position, profit, acc_profit, action;
    }

    public class TReportEntry
    {
        public string Name { get; set; }
        public string Value { get; set; }
        public string Value2 { get; set; }
        public string Value3 { get; set; }

        public TReportEntry(string name="", string val="", string val2 = "", string val3 = "")
        {
            Name = name;
            Value = val;
            Value2 = val2;
            Value3 = val3;
        }
    }
}
