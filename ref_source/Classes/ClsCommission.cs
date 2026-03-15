using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using VisualPortfolio.Classes;

namespace VisualPortfolio
{
    public class ClsCommissionSet
    {
        public ClsCommissionCfg cfg = new ClsCommissionCfg();
        public List<ClsCommissionYear> listYear = new List<ClsCommissionYear>();
        public decimal _profit = 0;
        public void BuildCommissionYears()
        {
            _profit = 0;
            listYear.Clear();
            List<ClsTradeItem> plist = Global.PortfolioList;

            var groupedByYear = plist.GroupBy(item => item.tradeDate2.Year);
            foreach (var yearGroup in groupedByYear)
            {
                List<ClsTradeItem> pyear = yearGroup.ToList();
                ClsCommissionYear cyear = CalcCommissionYear(pyear);
                listYear.Add(cyear);
            }
        }

        private ClsCommissionYear CalcCommissionYear(List<ClsTradeItem> plist)
        {
            var cfg = Global.CommissionSet.cfg;
            ClsCommissionYear cyear = new ClsCommissionYear();
            int year = plist[0].tradeDate2.Year;

            cyear.年度 = $"Year {year}";

            var groupedByQuarter = plist.GroupBy(item => (item.tradeDate2.Month+2)/3);

            decimal level = cfg.資金槓桿;
            decimal capital = cfg.初始資金;
            decimal refCap = cfg.回測金額;
            ClsCommissionEntry ce;
            foreach (var yearGroup in groupedByQuarter)
            {
                List<ClsTradeItem> pquart = yearGroup.ToList();
                ce = CalcCommissionQuarter(pquart, refCap, ref capital, level);
                cyear.ListEntry.Add(ce);
            }
            ce = new ClsCommissionEntry { 季別 = "全年" };
            ce.季初資金 = cyear.ListEntry[0].季初資金;
            ce.季末資金 = cyear.ListEntry.Last().季末資金;
            ce.分潤 = cyear.ListEntry.Sum(x => x.分潤);
            ce.手續費退傭 = cyear.ListEntry.Sum(x => x.手續費退傭);
            cyear.ListEntry.Add(ce);

            cyear.年度績效 = ce.客戶淨獲利 / ce.季初資金;
            cyear.獎金級距 = GetYearBonusRate(cfg, cyear.年度績效);
            cyear.績效獎金 = ce.客戶淨獲利 * cyear.獎金級距;
            cyear.綜合收入 = cyear.績效獎金 + ce.手續費退傭 + ce.分潤;

            return cyear;
        }

        private decimal GetYearBonusRate(ClsCommissionCfg cfg, decimal perf)
        {
            if (cfg.績效門檻4 > 0 && perf * 100 >= cfg.績效門檻4)
                return cfg.獎金比例4 * 0.01m;
            else if (cfg.績效門檻3 > 0 && perf * 100 >= cfg.績效門檻3)
                return cfg.獎金比例3 * 0.01m;
            else if (cfg.績效門檻2 > 0 && perf * 100 >= cfg.績效門檻2)
                return cfg.獎金比例2 * 0.01m;
            else if (cfg.績效門檻1 > 0 && perf * 100 >= cfg.績效門檻1)
                return cfg.獎金比例1 * 0.01m;
            else
                return 0;
        }

        private decimal SafeDoubleToDecimal(double val, decimal def = 0)
        {
            try
            {
                return (decimal)val;
            }
            catch { }
            return def;
        }

        private static readonly string[] qstr = new string[] { "第一季", "第二季", "第三季", "第四季" };
        private ClsCommissionEntry CalcCommissionQuarter(List<ClsTradeItem> plist, decimal refCap, ref decimal cap, decimal level)
        {
            var cfg = Global.CommissionSet.cfg;
            ClsCommissionEntry ce = new ClsCommissionEntry();
            ce.季別 = qstr[(plist[0].tradeDate2.Month - 1) / 3];
            ce.季初資金 = cap;
            double cap_d = (double)cap;
            double total_vol = 0;

            var groupByWeek = plist.GroupBy(x => GetWeekStartDate(x.tradeDate2));

            // You can now iterate through each weekly group.
            foreach (var weeklyGroup in groupByWeek)
            {
                var wlist = weeklyGroup.ToList();
                double profit = wlist.Sum(x => (double)x.netProfit * (double)x.aux_count * (double)x.aux_weight);
                double vol = wlist.Sum(x => (double)x.tradeAmount * (double)x.aux_count * (double)x.aux_weight);

                double r = cap_d * (double)level / (double)refCap;
                cap_d += r * profit / 10000;       // 因為我們用萬為單位
                total_vol += r * vol / 10000;   // 因為我們用萬為單位
            }

            cap = SafeDoubleToDecimal(cap_d);
            ce.季末資金 = cap;
            _profit += ce.獲利;
            if (_profit > 0)
            {
                ce.分潤 = _profit * cfg.季分潤 * 0.01m;
                _profit = 0;
            }

            double 退傭 = total_vol * (double) cfg.幣安手續費 * (double)cfg.手續費退傭 * 0.0001;  // 兩個%
            ce.手續費退傭 = SafeDoubleToDecimal(退傭);

            return ce;
        }

        private DateTime GetWeekStartDate(DateTime dt)
        {
            // The formula ((int)dt.DayOfWeek + 6) % 7 calculates the number of days
            // to subtract from the current date to get back to Monday.
            // .NET DayOfWeek: Sunday=0, Monday=1, Tuesday=2, ... Saturday=6.
            int daysToSubtract = ((int)dt.DayOfWeek + 6) % 7;
            return dt.Date.AddDays(-daysToSubtract);
        }
    }

    public class ClsCommissionYear
    {
        public string 年度 { get; set; }
        public decimal 年度績效 { get; set; }
        public decimal 獎金級距 { get; set; }
        public decimal 績效獎金 { get; set; }
        public decimal 綜合收入 { get; set; }
        public List<ClsCommissionEntry> ListEntry { get; set; } = new List<ClsCommissionEntry>();
    }

    public class ClsCommissionEntry
    {
        public string 季別 { get; set; }
        public decimal 季初資金 { get; set; }
        public decimal 季末資金 { get; set; }
        public decimal 獲利 => 季末資金 - 季初資金;
        public decimal 季績效 => 季初資金 > 0 ? 獲利 / 季初資金 : 0;
        public decimal 分潤 { get; set; }
        public decimal 客戶淨獲利 => 獲利 - 分潤;
        public decimal 手續費退傭 { get; set; }
    }

    public class ClsCommissionCfg : ClsProperty
    {
        [DisplayName("回測金額(萬)")]
        public decimal 回測金額 { get; set; } = 1000;
        [DisplayName("初始資金(萬)")]
        public decimal 初始資金 { get; set; } = 1000;
        [DisplayName("資金槓桿")]
        public decimal 資金槓桿 { get; set; } = 3;
        [DisplayName("幣安手續費(%)")]
        public decimal 幣安手續費 { get; set; } = 0.05m;
        [DisplayName("手續費退傭(%)")]
        public decimal 手續費退傭 { get; set; } = 30;
        [DisplayName("季分潤(%)")]
        public decimal 季分潤 { get; set; } = 30;
        [DisplayName("績效門檻1(%)"), Description("可設0，表示無作用")]
        public decimal 績效門檻1 { get; set; } = 100;
        [DisplayName("獎金比例1(%)")]
        public decimal 獎金比例1 { get; set; } = 10;
        [DisplayName("績效門檻2(%)"), Description("可設0，表示無作用")]
        public decimal 績效門檻2 { get; set; } = 150;
        [DisplayName("獎金比例2(%)")]
        public decimal 獎金比例2 { get; set; } = 20;
        [DisplayName("績效門檻3(%)"), Description("可設0，表示無作用")]
        public decimal 績效門檻3 { get; set; } = 200;
        [DisplayName("獎金比例3(%)")]
        public decimal 獎金比例3 { get; set; } = 30;
        [DisplayName("績效門檻4(%)"), Description("可設0，表示無作用")]
        public decimal 績效門檻4 { get; set; } = 0;
        [DisplayName("獎金比例4(%)")]
        public decimal 獎金比例4 { get; set; } = 0;
    }
}
