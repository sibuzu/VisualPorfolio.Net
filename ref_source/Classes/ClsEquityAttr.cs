using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text;

namespace VisualPortfolio.Classes
{
    public class ClsEquityAttr
    {
        [DisplayName("啟動")]
        public bool Active { get; set; }
        [DisplayName("No."), ReadOnly(true)]
        public int Index { get; set; }
        [DisplayName("顏色"), Browsable(false)]
        public Color Color { get; set; }
        [DisplayName("口數")]
        public int Contract { get; set; }
        [DisplayName("權重")]
        public decimal Weight { get; set; }
        [DisplayName("檔案")]
        public string BaseFileName
        {
            get
            {
                return Path.GetFileNameWithoutExtension(FileName);
            }
        }
        [Browsable(false), ReadOnly(true)]
        public string FileName { get; set; }

        public string 名稱 { get; set; }

        public string GetName() { return string.IsNullOrEmpty(名稱) ? BaseFileName : 名稱; }

        public ClsTradeList TradeList;
        public ClsEquityAttr()
        {
            TradeList = new ClsTradeList();
        }

        internal static ClsEquityAttr CreateFixProfit(DateTime start, DateTime end, decimal profit, int idx, Color c)
        {
            var ea = new ClsEquityAttr();

            ea.FileName = $"FixProfit_{profit}";
            ea.Index = idx;
            ea.Color = c;
            ea.Active = true;
            ea.Contract = 1;
            ea.Weight = 1;

            int start_ym = start.Year * 12 + start.Month;
            int end_ym = end.Year * 12 + end.Month;
            int tidx = 0;
            for (int ym = start_ym; ym < end_ym; ++ym)
            {
                DateTime dt = new DateTime(ym / 12, ym % 12 + 1, 1);
                var item = new ClsTradeItem();
                item.idx = ++tidx;
                item.tradeDate1 = dt;
                item.tradeDate2 = dt;
                item.price2 = Math.Abs(profit) + 1;
                item.pointValue = 1;
                item.bs = 'B';
                item.contract = dt.Year * 100 + dt.Month;
                item.profit = profit;
                item.netProfit = item.profit;

                ea.TradeList.Items.Add(item);
            }

            return ea;
        }
    }
}
