using NPlot;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using VisualPortfolio;
using VisualPortfolio.Classes;
using WeifenLuo.WinFormsUI.Docking;
using NPlot.Windows;

namespace VisualPortfolio.Forms
{
    public enum enumProfitDrawdown
    {
        Profit,
        Drawdown
    }

    public partial class FormSimpleMonth : DockContent
    {
        public FormSimpleMonth()
        {
            InitializeComponent();
            cbKind.SelectedIndex = 2;
            cbInterval.SelectedIndex = 0;
        }

        private int GetInterval(int select)
        {
            switch(select)
            {
                case 0:
                    return 12;
                case 1:
                    return 6;
                case 2:
                    return 4;
                case 3:
                    return 3;
                case 4:
                    return 2;
                case 5:
                    return 1;
                default:
                    return 1;
            }
        }

        private bool IsByYear(int select)
        {
            return (select >= GetDefaultIntervalCount());
        }

        private int GetDefaultIntervalCount()
        {
            return 6;
        }

        public void CreatePlot()
        {
            var surf = surfProfitMonth;

            List<int> years = new List<int>();
            List<int> months = new List<int>();
            List<double> yearProfits = new List<double>();
            List<double> monthProfits = new List<double>();
            List<double> yearMDD = new List<double>();
            List<double> monthMDD = new List<double>();

            var lp = Global.PortfolioList;
            var factor = Global.listEquityAttr.ContractFactor;

            UpdateYearCombo(cbInterval, lp);

            surf.Clear();
            if (lp.Count == 0) return;


            int year = 0;
            bool byYear = IsByYear(cbInterval.SelectedIndex); 
            int minterval = GetInterval(cbInterval.SelectedIndex);
            if (byYear)
            {
                year = int.Parse(cbInterval.Text);
            }

            TSummaryReport.CalcYearMonthProfit(lp, factor, minterval, years, months, yearProfits, monthProfits, yearMDD, monthMDD);

            int rolling = (int) spinRolling.Value;
            yearProfits = CalcRolling(yearProfits, rolling);
            monthProfits = CalcRolling(monthProfits, rolling);

            switch (cbKind.SelectedIndex)
            {
                case 0: // Profit
                    if (year == 0)
                        CreateBarPlot(surfProfitMonth, year, years, yearProfits, Color.Blue);
                    else
                        CreateBarPlot(surfProfitMonth, year, months, monthProfits, Color.Blue);
                    break;
                case 1: // Drawdown
                    if (year == 0)
                        CreateBarPlot(surfProfitMonth, year, years, yearMDD, Color.Red);
                    else
                        CreateBarPlot(surfProfitMonth, year, months, monthMDD, Color.Red);
                    break;
                case 2: // Profit + Drawdown
                    if (year == 0)
                        CreateBarPlot2(surfProfitMonth, minterval, year, years, yearProfits, yearMDD);
                    else
                        CreateBarPlot2(surfProfitMonth, minterval, year, months, monthProfits, monthMDD);
                    break;
                case 3: // Profit(Sep)
                    if (year == 0)
                        CreateYearProfitsPlot(surfProfitMonth, minterval, enumProfitDrawdown.Profit);
                    else
                        CreateMonthProfitsPlot(surfProfitMonth, minterval, year, enumProfitDrawdown.Profit);
                    break;
                case 4: // MDD(Sep)
                    if (year == 0)
                        CreateYearProfitsPlot(surfProfitMonth, minterval, enumProfitDrawdown.Drawdown);
                    else
                        CreateMonthProfitsPlot(surfProfitMonth, minterval, year, enumProfitDrawdown.Drawdown);
                    break;
            }
            surfProfitMonth.Invalidate();
        }

        private List<double> CalcRolling(List<double> profits, int rolling)
        {
            if (rolling == 1) return profits;

            int n = profits.Count;
            var plist = new List<double>();
            for (int i=0; i<n; ++i)
            {
                double sum = 0;
                int c = 0;
                for (int j=i; j<i+rolling && j<n; j++)
                {
                    sum += profits[j];
                    c++;
                }

                plist.Add(sum / c);
            }

            return plist;
        }

        private void UpdateYearCombo(ComboBox cb, List<ClsTradeItem> lp)
        {
            int defN = GetDefaultIntervalCount();
            if (lp.Count == 0)
            {
                if (cb.Items.Count != defN)
                {
                    PrepareDefaultInverval(cb);
                    cb.SelectedIndex = 0;
                }
                return;
            }

            int minYear = lp[0].tradeDate2.Year;
            int maxYear = lp[lp.Count - 1].tradeDate2.Year;
            int count = maxYear - minYear + 1;

            string txt = cb.Text;
            if (cb.Items.Count == count + defN && cb.Items[defN].ToString() == minYear.ToString())
            {
                // the same, just return;
                return;
            }

            PrepareDefaultInverval(cb);
            for (int yr = minYear; yr<=maxYear; ++yr)
            {
                cb.Items.Add(yr.ToString());
            }

            int idx = cb.Items.IndexOf(txt);
            if (idx < 0) idx = 0;
            cb.SelectedIndex = idx;
        }

        private static void PrepareDefaultInverval(ComboBox cb)
        {
            cb.Items.Clear();
            cb.Items.Add("全部(每年)");
            cb.Items.Add("全部(每半年)");
            cb.Items.Add("全部(每4月)");
            cb.Items.Add("全部(每3月)");
            cb.Items.Add("全部(每2月)");
            cb.Items.Add("全部(每月)");
        }

        private HistogramPlot CreateBar(List<int> xvals, List<double> yvals, Color c, float bw, TimeSpan offset)
        {
            int n = xvals.Count;
            if (n == 0) return null;

            DateTime[] xp = new DateTime[n];
            double[] yp = new double[n];

            for (int i = 0; i < n; ++i)
            {
                xp[i] = new DateTime(xvals[i] / 100, xvals[i] % 100, 1) + offset;
                yp[i] = yvals[i];
            }

            HistogramPlot bp = new HistogramPlot();
            bp.AbscissaData = xp;
            bp.OrdinateData = yp;
            bp.RectangleBrush = new NPlot.RectangleBrushes.Solid(c);
            bp.Filled = true;
            bp.BaseWidth = bw;
            return bp;
        }

        private void CreateBarPlot(NPlot.Windows.PlotSurface2D surf, int year, List<int> xvals, List<double> yvals, Color c)
        {
            int n = xvals.Count;

            if (year != 0)
            {
                List<int> xtmp = new List<int>();
                List<double> ytmp = new List<double>();
                for (int i = 0; i < n; ++i)
                {
                    if (xvals[i] / 100 == year)
                    {
                        xtmp.Add(xvals[i]);
                        ytmp.Add(yvals[i]);
                    }
                }

                xvals = xtmp;
                yvals = ytmp;
                n = xvals.Count;
            }

            if (n == 0) return;

            string xtitle = (year == 0) ? "Years" : "Year = " + year.ToString();
            string ytitle = (cbKind.SelectedIndex == 0) ? "Profit" : "Drawdown";
            string xfmt = (cbInterval.SelectedIndex==0) ? "yyyy" : "yyyy/MM";
            string yfmt = "${0:#,##0}";

            // grid
            Grid myGrid = new Grid();
            myGrid.HorizontalGridType = Grid.GridType.Fine;
            myGrid.VerticalGridType = Grid.GridType.Coarse;
            myGrid.MajorGridPen = new Pen(Color.DarkGray);
            myGrid.MajorGridPen.DashStyle = System.Drawing.Drawing2D.DashStyle.Dash;
            surf.Add(myGrid);

            HistogramPlot bp = CreateBar(xvals, yvals, c, 0.7f, new TimeSpan());
            surf.Add(bp);

            HorizontalLine line = new HorizontalLine(0, Color.Blue);
            surf.Add(line);

            SetupAxis(surf, xtitle, ytitle, xfmt, yfmt);
        }

        private void CreateBarPlot2(NPlot.Windows.PlotSurface2D surf, int mi, int year, List<int> xvals, List<double> y1vals, List<double> y2vals)
        {
            int n = xvals.Count;

            if (year > 0)
            {
                List<int> xtmp = new List<int>();
                List<double> y1tmp = new List<double>();
                List<double> y2tmp = new List<double>();
                for (int i = 0; i < n; ++i)
                {
                    if (xvals[i] / 100 == year)
                    {
                        xtmp.Add(xvals[i]);
                        y1tmp.Add(y1vals[i]);
                        y2tmp.Add(y2vals[i]);
                    }
                }

                xvals = xtmp;
                y1vals = y1tmp;
                y2vals = y2tmp;
                n = xvals.Count;
            }

            if (n == 0) return;
            string xtitle = (year == 0) ? "Years" : "Year = " + year.ToString();
            string ytitle = "Profit / Drawdown";
            string xfmt = (cbInterval.SelectedIndex == 0) ? "yyyy" : "yyyy/MM";
            string yfmt = "${0:#,##0}";

            // grid
            Grid myGrid = new Grid();
            myGrid.HorizontalGridType = Grid.GridType.Fine;
            myGrid.VerticalGridType = Grid.GridType.Coarse;
            myGrid.MajorGridPen = new Pen(Color.DarkGray);
            myGrid.MajorGridPen.DashStyle = System.Drawing.Drawing2D.DashStyle.Dash;
            surf.Add(myGrid);

            float bw = 0.7f / 2;
            TimeSpan offset = new TimeSpan(130 * mi, 0, 0);

            HistogramPlot bp;

            bp = CreateBar(xvals, y1vals, Color.Blue, bw, -offset);
            surf.Add(bp);
            bp = CreateBar(xvals, y2vals, Color.Red, bw, offset);
            surf.Add(bp);

            HorizontalLine line = new HorizontalLine(0, Color.Blue);
            surf.Add(line);

            SetupAxis(surf, xtitle, ytitle, xfmt, yfmt);
        }

        private void CreateYearProfitsPlot(NPlot.Windows.PlotSurface2D surf, int mi, enumProfitDrawdown pd)
        {
            List<ClsEquityAttr> listEquity = new List<ClsEquityAttr>();
            foreach (var ea in Global.listEquityAttr)
            {
                if (!ea.Active) continue;
                listEquity.Add(ea);
            }

            int n = listEquity.Count;
            if (n == 0) return;

            string xtitle = "Years";
            string ytitle = (pd==enumProfitDrawdown.Profit) ? "Profit" : "Drawdown";
            string xfmt = (cbInterval.SelectedIndex == 0) ? "yyyy" : "yyyy/MM";
            string yfmt = "${0:#,##0}";

            // grid
            Grid myGrid = new Grid();
            myGrid.HorizontalGridType = Grid.GridType.Fine;
            myGrid.VerticalGridType = Grid.GridType.Coarse;
            myGrid.MajorGridPen = new Pen(Color.DarkGray);
            myGrid.MajorGridPen.DashStyle = System.Drawing.Drawing2D.DashStyle.Dash;
            surf.Add(myGrid);

            for (int i = 0; i < n; ++i)
            {
                var ea = listEquity[i];
                var itemList = ea.TradeList.Items;
                var plist = new List<ClsTradeItem>();

                foreach (ClsTradeItem ti in itemList)
                {
                    ti.tag = i;
                    ti.aux_count = ea.Contract;
                    ti.aux_weight = ea.Weight;
                    plist.Add(ti);
                }

                if (plist.Count < 2) continue;
                double factor = Global.listEquityAttr.DivByCount ? 1.0 / ea.Contract : 1;

                List<int> years = new List<int>();
                List<int> months = new List<int>();
                List<double> yearProfits = new List<double>();
                List<double> monthProfits = new List<double>();
                List<double> yearMDD = new List<double>();
                List<double> monthMDD = new List<double>();

                TSummaryReport.CalcYearMonthProfit(plist, factor, mi, years, months, yearProfits, monthProfits, yearMDD, monthMDD);
                int rolling = (int)spinRolling.Value;
                yearProfits = CalcRolling(yearProfits, rolling);

                float bw = 0.7f / n;
                float hours = mi * (-1.0f + (i * 2.0f + 1.0f) / n) * 260f;
                TimeSpan offset = new TimeSpan((int)hours, 0, 0);
                HistogramPlot bp =
                    (pd == enumProfitDrawdown.Profit) ?
                    CreateBar(years, yearProfits, ea.Color, bw, offset) :
                    CreateBar(years, yearMDD, ea.Color, bw, offset);
                surf.Add(bp);
            }

            HorizontalLine line = new HorizontalLine(0, Color.Blue);
            surf.Add(line);

            SetupAxis(surf, xtitle, ytitle, xfmt, yfmt);
        }

        private void CreateMonthProfitsPlot(NPlot.Windows.PlotSurface2D surf, int mi, int year, enumProfitDrawdown pd)
        {
            List<ClsEquityAttr> listEquity = new List<ClsEquityAttr>();
            foreach (var ea in Global.listEquityAttr)
            {
                if (!ea.Active) continue;
                listEquity.Add(ea);
            }

            int n = listEquity.Count;
            if (n == 0) return;

            string xtitle = "Year = " + year.ToString();
            string ytitle = (pd == enumProfitDrawdown.Profit) ? "Profit" : "Drawdown";
            string xfmt = "yyyy/MM";
            string yfmt = "${0:#,##0}";

            // grid
            Grid myGrid = new Grid();
            myGrid.HorizontalGridType = Grid.GridType.Fine;
            myGrid.VerticalGridType = Grid.GridType.Coarse;
            myGrid.MajorGridPen = new Pen(Color.DarkGray);
            myGrid.MajorGridPen.DashStyle = System.Drawing.Drawing2D.DashStyle.Dash;
            surf.Add(myGrid);

            for (int i = 0; i < n; ++i)
            {
                var ea = listEquity[i];
                var itemList = ea.TradeList.Items;
                var plist = new List<ClsTradeItem>();

                foreach (ClsTradeItem ti in itemList)
                {
                    ti.tag = i;
                    ti.aux_count = ea.Contract;
                    ti.aux_weight = ea.Weight;
                    plist.Add(ti);
                }

                if (plist.Count < 2) continue;
                double factor = Global.listEquityAttr.DivByCount ? 1.0 / ea.Contract : 1;

                List<int> years = new List<int>();
                List<int> months = new List<int>();
                List<double> yearProfits = new List<double>();
                List<double> monthProfits = new List<double>();
                List<double> yearMDD = new List<double>();
                List<double> monthMDD = new List<double>();

                TSummaryReport.CalcYearMonthProfit(plist, factor, mi, years, months, yearProfits, monthProfits, yearMDD, monthMDD);
                int rolling = (int)spinRolling.Value;
                monthProfits = CalcRolling(monthProfits, rolling);

                var monthVals = (pd == enumProfitDrawdown.Profit) ? monthProfits : monthMDD;

                List <int> xvals = new List<int>();
                List<double> yvals = new List<double>();
                for (int k = 0; k < months.Count; ++k)
                {
                    if (months[k] / 100 == year)
                    {
                        xvals.Add(months[k]);
                        yvals.Add(monthVals[k]);
                    }
                }

                float bw = 0.7f / n;
                float hours = mi * (-1.0f + (i * 2.0f + 1.0f) / n) * 260f;
                TimeSpan offset = new TimeSpan((int)hours, 0, 0);
                HistogramPlot bp = CreateBar(xvals, yvals, ea.Color, bw, offset);
                surf.Add(bp);
            }

            HorizontalLine line = new HorizontalLine(0, Color.Blue);
            surf.Add(line);

            SetupAxis(surf, xtitle, ytitle, xfmt, yfmt);
        }

        private void SetupAxis(NPlot.Windows.PlotSurface2D surf,
           string xtitle, string ytitle, string xfmt, string yfmt)
        {
            surf.Padding = 2;
            surf.XAxis1 = new DateTimeAxis(surf.XAxis1);
            surf.YAxis1 = new LinearAxis(surf.YAxis1);
            surf.YAxis2 = new LinearAxis(surf.YAxis1);
            surf.XAxis1.Label = xtitle;
            surf.XAxis1.NumberFormat = xfmt;
            surf.YAxis1.Label = ytitle;
            surf.YAxis1.NumberFormat = yfmt;
            surf.YAxis2.TicksAngle = -(float)Math.PI / 2.0f;
            surf.YAxis2.Label = " ";
            surf.YAxis2.LabelOffset = 40;
            surf.YAxis2.LabelOffsetAbsolute = true;
            surf.YAxis2.NumberFormat = yfmt;
        }

        private void cbKind_SelectedIndexChanged(object sender, EventArgs e)
        {
            CreatePlot();
        }

        private void btnCopy_Click(object sender, EventArgs e)
        {
            surfProfitMonth.CopyToClipboard();
        }

        private void btnSave_Click(object sender, EventArgs e)
        {
            SaveFileDialog dlg = new SaveFileDialog();
            dlg.Filter = "PNG Files|*.png|All Files|*.*";
            if (dlg.ShowDialog() == DialogResult.OK)
            {
                surfProfitMonth.CopyToClipboard();
                var b = Clipboard.GetImage();
                b.Save(dlg.FileName);
            }
        }
    }
}
