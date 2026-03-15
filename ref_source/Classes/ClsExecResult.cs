using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using VisualPortfolio.Classes;

namespace VisualPortfolio
{
    public class ClsExecResult
    {
        #region property
        public int Index { get; set; }
        public string 策略 { get; set; }
        public int 口數 { get; set; }
        [DisplayName("獲利(%)")]
        public decimal 獲利比 { get; set; }
        public decimal 獲利 { get; set; }
        public decimal MDD { get; set; }
        [DisplayName("獲利/MDD")]
        public decimal PMR { get; set; }
        [DisplayName("獲利(點)")]
        public string 獲利點 { get; set; }
        public string Weight { get; set; }
        public string PointValue { get; set; }
        #endregion
    }

    public class ClsExecResultList : BindingList<ClsExecResult>
    {
        internal void UpdateResult()
        {
            decimal total_profit = 0;

            Clear();
            // Global.RawPortfolioList.Clear();
            for (int i = 0; i < Global.listEquityAttr.Count; ++i)
            {
                ClsEquityAttr ea = Global.listEquityAttr[i];
                if (!ea.Active) continue;

                var dtStart = Global.frmEquityManage.GetRangeStart().Date;
                var dtEnd = Global.frmEquityManage.GetRangeEnd().Date + new TimeSpan(23,59,59);
                ClsTradeList tlist = ea.TradeList.CutDate(dtStart, dtEnd);

                ClsExecResult er = new ClsExecResult();
                er.Index = ea.Index;
                er.策略 = ea.GetName();
                er.口數 = ea.Contract;
                er.Weight = ea.Weight.ToString();
                er.PointValue = tlist.PointValue.ToString();
                er.獲利點 = (tlist.NetProfit / tlist.PointValue).ToString("#0.##");
                er.MDD = tlist.MDD * ea.Weight * ea.Contract;
                er.獲利 = tlist.NetProfit * ea.Weight * ea.Contract;
                er.PMR = er.MDD == 0 ? 0 : tlist.NetProfit / tlist.MDD;
                total_profit += er.獲利;

                this.Add(er);
            }

            if (this.Count > 0)
            {
                ClsExecResult er = new ClsExecResult();
                er.Index = 0;
                er.策略 = "ALL";
                er.獲利 = total_profit;
                er.MDD = Global.TotalMDD;
                er.PMR = er.MDD == 0 ? 0 : er.獲利 / er.MDD;
                er.獲利比 = 1;
                er.Weight = "-";
                er.獲利點 = "-";
                er.PointValue = "-";
                Insert(0, er);

                er.口數 = 0;
                for (int i = 1; i < Count; ++i)
                {
                    er.口數 += this[i].口數;
                }

                if (total_profit>0)
                {
                    for (int i=1; i<Count; ++i)
                    {
                        this[i].獲利比 = this[i].獲利 / total_profit;
                    }
                }

            }
        }
    }
}
