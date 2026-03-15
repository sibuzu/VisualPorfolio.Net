using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Xml;

namespace VisualPortfolio.Classes
{
    public class ClsWinLossRecord
    {
        public ClsWinLossRecord()
        {
            週期 = "";
            贏錢次數 = 0;
            輸錢次數 = 0;
            總贏錢 = 0;
            總輸錢 = 0;
        }

        public string 週期;
        public int 贏錢次數;
        public int 輸錢次數;
        public int 總次數
        {
            get
            {
                return 贏錢次數 + 輸錢次數;
            }
        }
        public double 贏錢機率
        {
            get
            {
                double n = 贏錢次數 + 輸錢次數;
                return n == 0 ? 0 : 贏錢次數 / n;
            }
        }
        public double profit;
        public double 總贏錢;
        public double 總輸錢;
        public double 最大贏錢;
        public double 最大輸錢;
        public double 平均每次贏錢
        {
            get
            {
                return 贏錢次數 == 0 ? 0 : 總贏錢 / 贏錢次數;
            }
        }
        public double 平均每次輸錢
        {
            get
            {
                return 輸錢次數 == 0 ? 0 : 總輸錢 / 輸錢次數;
            }
        }
        public double 每次贏輸比
        {
            get
            {
                return 平均每次輸錢 == 0 ? 1 : 平均每次贏錢 / 平均每次輸錢;
            }
        }
        public double 全部贏輸比
        {
            get
            {
                return 總輸錢 == 0 ? 1 : 總贏錢 / 總輸錢;
            }
        }
    }

    public class ClsWinLossList
    {
        public List<ClsWinLossRecord> Items;
        private List<ClsWinLossRecord> _sumItems;
        private DateTime _lastDate;

        public ClsWinLossList()
        {
            Clear();
        }

        public void Clear()
        {
            _lastDate = DateTime.MinValue;
            string[] names = new string[] { "日", "週", "月", "年" };
            Items = new List<ClsWinLossRecord>();
            _sumItems = new List<ClsWinLossRecord>();

            for (int i = 0; i < 4; i++)
            {
                var rec = new ClsWinLossRecord();
                rec.週期 = names[i];
                Items.Add(rec);
                var rec2 = new ClsWinLossRecord();
                _sumItems.Add(rec2);
            }
        }

        internal void Update(ClsTradeItem ti)
        {
            for (int i=0; i<4; ++i)
            {
                UpdateItem(i, ti, Items[i], _sumItems[i]);
            }

            _lastDate = ti.tradeDate2;
        }

        private void UpdateItem(int i, ClsTradeItem pr, ClsWinLossRecord item, ClsWinLossRecord sumItem)
        {
            double profit = (double)pr.netProfit * (double)pr.aux_count * (double)pr.aux_weight;
            if (IsSameRecord(i, _lastDate, pr.tradeDate2))
            {
                sumItem.贏錢次數 += 1;
                sumItem.profit += profit;
            }
            else
            {
                if (sumItem.贏錢次數 > 0)
                {
                    if (sumItem.profit > 0)
                    {
                        item.贏錢次數 += 1;
                        item.總贏錢 += sumItem.profit;
                        item.最大贏錢 = Math.Max(item.最大贏錢, sumItem.profit);
                    }
                    else
                    {
                        item.總輸錢 += -sumItem.profit;
                        item.輸錢次數 += 1;
                        item.最大輸錢 = Math.Max(item.最大輸錢, -sumItem.profit);
                    }
                }
                sumItem.贏錢次數 = 1;
                sumItem.profit = profit;
            }
        }

        private bool IsSameRecord(int i, DateTime dt1, DateTime dt2)
        {
            switch (i)
            {
                case 0:
                    return IsSameDay(dt1, dt2);
                case 1:
                    return IsSameWeek(dt1, dt2);
                case 2:
                    return IsSameMonth(dt1, dt2);
                default:
                    return IsSameYear(dt1, dt2);
            }
        }

        private bool IsSameDay(DateTime dt1, DateTime dt2)
        {
            return dt1.Date == dt2.Date;
        }

        private bool IsSameWeek(DateTime dt1, DateTime dt2)
        {
            int n1 = (dt1.Date - new DateTime(2010, 8, 1)).Days; // SunDay
            int n2 = (dt2.Date - new DateTime(2010, 8, 1)).Days; // SunDay
            return (n1 / 7 == n2 / 7);
        }

        private bool IsSameMonth(DateTime dt1, DateTime dt2)
        {
            return (dt1.Year == dt2.Year) && (dt1.Month == dt2.Month);
        }

        private bool IsSameYear(DateTime dt1, DateTime dt2)
        {
            return dt1.Year == dt2.Year;
        }

        internal void FinalUpdate()
        {
            ClsTradeItem pr = new ClsTradeItem();
            pr.tradeDate2 = DateTime.MaxValue;
            this.Update(pr);
        }
    }

    public class ClsWinLossRow
    {
        public string 項目 { get; set; }
        public string 日 { get; set; }
        public string 週 { get; set; }
        public string 月 { get; set; }
        public string 年 { get; set; }
    }
}