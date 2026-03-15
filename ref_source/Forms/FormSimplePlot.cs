using NPlot;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using VisualPortfolio.Classes;
using WeifenLuo.WinFormsUI.Docking;

namespace VisualPortfolio.Forms
{
    public partial class FormSimplePlot : DockContent
    {
        private DateTime[] _profit_date = null;
        private decimal[] _profit_price = null;
        private decimal[] _drawdown_price = null;

        public FormSimplePlot()
        {
            InitializeComponent();
            cbKind.SelectedIndex = 0;
            cbInterval.SelectedIndex = 0;
        }

        private void UpdateYearCombo(ComboBox cb, List<ClsTradeItem> lp)
        {
            if (lp.Count == 0)
            {
                if (cb.Items.Count != 1)
                {
                    cb.Items.Clear();
                    cb.Items.Add("全部");
                    cb.SelectedIndex = 0;
                }
                return;
            }

            int minYear = lp[0].tradeDate2.Year;
            int maxYear = lp[lp.Count - 1].tradeDate2.Year;
            int count = maxYear - minYear + 1;

            string txt = cb.Text;
            if (cb.Items.Count == count + 1 && cb.Items[1].ToString() == minYear.ToString())
            {
                // the same, just return;
                return;
            }

            cb.Items.Clear();
            cb.Items.Add("全部");
            for (int yr = minYear; yr <= maxYear; ++yr)
            {
                cb.Items.Add(yr.ToString());
            }

            int idx = cb.Items.IndexOf(txt);
            if (idx < 0) idx = 0;
            cb.SelectedIndex = idx;
        }

        public void CreatePlot()
        {
            UpdateYearCombo(cbInterval, Global.PortfolioList);

            List<ClsTradeItem> plist = null;
            if (cbInterval.Text == "全部" || cbInterval.Text == "")
            {
                plist = Global.PortfolioList;
            }
            else
            {
                int year = int.Parse(cbInterval.Text);
                plist = new List<ClsTradeItem>();
                foreach (var ti in Global.PortfolioList)
                {
                    if (ti.tradeDate2.Year == year)
                        plist.Add(ti);
                }
            }

            switch (cbKind.SelectedIndex)
            {
                case 0: // Profit
                case 1: // Profit
                case 2: // Profit
                    CreatePlotTotalProfit(surfProfitSimple, plist, cbKind.SelectedIndex);
                    break;
                case 3: // drawdown
                    CreatePlotDrawdown(surfProfitSimple, plist);
                    break;
            }
            surfProfitSimple.Invalidate();
        }

        public LinePlot AddLine(NPlot.Windows.PlotSurface2D surf, List<ClsTradeItem> plist, decimal factor)
        {
            int n = plist.Count;
            var price = new decimal[n];
            var date = new DateTime[n];
            decimal profit = 0;
            decimal total_profit = 0;

            for (int i = 0; i < n; ++i)
            {
                profit = plist[i].netProfit * factor * plist[i].aux_count * plist[i].aux_weight;
                total_profit += profit;
                price[i] += total_profit;
                date[i] = plist[i].tradeDate2;
            }

            for (int i=n-2; i>=0; --i)
            {
                if (date[i].Date==date[i+1].Date)
                {
                    price[i] = price[i + 1];
                }
            }

            LinePlot lp = new LinePlot();
            lp.AbscissaData = date;
            lp.OrdinateData = price;

            return lp;
        }

        public void CreatePlotTotalProfit(NPlot.Windows.PlotSurface2D surf, List<ClsTradeItem> plist, int kind)
        {
            surf.Clear();
            if (plist == null || plist.Count == 0) return;

            decimal factor = (decimal)Global.listEquityAttr.ContractFactor;
            bool drawDD = (kind == 0) && (plist.Count == Global.PortfolioList.Count);
            bool drawTotal = (kind == 0 || kind == 2);
            bool drawSep = (kind == 1 || kind == 2);
            bool drawed = drawTotal;


            // grid
            Grid myGrid = new Grid();
            myGrid.HorizontalGridType = Grid.GridType.Fine;
            myGrid.VerticalGridType = Grid.GridType.Coarse;
            myGrid.MajorGridPen = new Pen(Color.DarkGray);
            myGrid.MajorGridPen.DashStyle = System.Drawing.Drawing2D.DashStyle.Dash;
            surf.Add(myGrid);


            string xlabel = "Trade Date";
            string ylabel = "Profit ($)";
            string xfmt = "yyyy/MM";
            string yfmt = "${0:#,##0.##}";

            var lp = AddLine(surf, plist, factor);
            if (lp == null) return;

            _profit_date = (DateTime[])lp.AbscissaData;
            _profit_price = (decimal[])lp.OrdinateData;
            lp.Color = Color.Black;
            if (drawTotal) surf.Add(lp);

            if (drawSep && _profit_date.Length > 0)
            {
                DateTime start_date = _profit_date[0].Date;
                DateTime end_date = _profit_date[_profit_date.Length-1].Date;
                for (int i = 0; i < Global.listEquityAttr.Count; ++i)
                {
                    var ea = Global.listEquityAttr[i];
                    if (!ea.Active) continue;

                    var itemList = ea.TradeList.Items;
                    plist = new List<ClsTradeItem>();

                    foreach (ClsTradeItem ti in itemList)
                    {
                        if (ti.tradeDate2.Date < start_date) continue;
                        if (ti.tradeDate2.Date > end_date) break;
                        ti.tag = i;
                        ti.aux_count = ea.Contract;
                        ti.aux_weight = ea.Weight;
                        plist.Add(ti);
                    }

                    if (plist.Count < 2) return;

                    factor = Global.listEquityAttr.DivByCount ? 1m / ea.Contract : 1;

                    lp = AddLine(surf, plist, factor);
                    lp.Color = ea.Color;
                    surf.Add(lp, -1);
                    drawed = true;
                }
            }

            HorizontalLine line = new HorizontalLine(0, Color.Blue);
            surf.Add(line);

            if (!drawed) return;
            SetupAxis(surf, xlabel, ylabel, xfmt, yfmt);

            // DrawMDD Line
            if (drawDD && Global.SummaryReport.listMDD != null)
            {
                for (int i = 0; i < Global.MddCount && i < Global.SummaryReport.listMDD.Count; ++i)
                {
                    ClsMDD mdd = Global.SummaryReport.listMDD[i];
                    int x1 = mdd.StartIdx;
                    int x2 = mdd.EndIdx;
                    int x3 = mdd.EndIdx2;
                    Drawline(surf, x1, x3, x1);
                    Drawline(surf, x1, x2, x2);
                }
            }
        }

        public void CreatePlotDrawdown(NPlot.Windows.PlotSurface2D surf, List<ClsTradeItem> plist)
        {
            surf.Clear();
            if (plist == null || plist.Count == 0) return;
            decimal factor = (decimal)Global.listEquityAttr.ContractFactor;

            int n = plist.Count;
            int[] x = new int[n];
            _drawdown_price = new decimal[n];
            _profit_date = new DateTime[n];
            decimal profit = 0;
            decimal drawdown = 0;

            for (int i = 0; i < n; ++i)
            {
                x[i] = i;
                profit = plist[i].netProfit * factor * plist[i].aux_count * plist[i].aux_weight;

                _profit_date[i] = plist[i].tradeDate2;
                drawdown -= profit;
                if (drawdown < 0) drawdown = 0;
                _drawdown_price[i] = drawdown;
            }

            // grid
            Grid myGrid = new Grid();
            myGrid.HorizontalGridType = Grid.GridType.Fine;
            myGrid.VerticalGridType = Grid.GridType.Coarse;
            myGrid.MajorGridPen = new Pen(Color.DarkGray);
            myGrid.MajorGridPen.DashStyle = System.Drawing.Drawing2D.DashStyle.Dash;
            surf.Add(myGrid);

            HorizontalLine line = new HorizontalLine(0, Color.Blue);
            surf.Add(line);

            LinePlot lp = new LinePlot();
            string xlabel = "Trade Date";
            string ylabel = "Drawdown ($)";
            string xfmt = "yyyy/MM";
            string yfmt = "${0:#,##0.##}";

            lp.AbscissaData = _profit_date;
            lp.OrdinateData = _drawdown_price;
            ylabel = "Drawdown ($)";

            surf.Add(lp);
            SetupAxis(surf, xlabel, ylabel, xfmt, yfmt);
        }

        private void Drawline(NPlot.Windows.PlotSurface2D surf, int start, int end, int value)
        {
            LinePlot lpp = new LinePlot();
            lpp.Pen = new Pen(Color.Red);
            lpp.AbscissaData = new DateTime[] { _profit_date[start], _profit_date[end] };
            lpp.OrdinateData = new decimal[] { _profit_price[value], _profit_price[value] };
            surf.Add(lpp);
        }

        private void SetupAxis(NPlot.Windows.PlotSurface2D surf,
            string xtitle, string ytitle, string xfmt, string yfmt)
        {
            surf.Padding = 2;
            surf.Title = Global.GetPlotTitle();
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

        int reenter = 0;
        int retry = 0;
        private string GetPlotTipString(double x, double y)
        {
            if (reenter > 0)
            {
                retry++;
                if (retry < 10) return "";
            }

            retry = 0;
            reenter = 1;
            string s = "";

            try
            {
                int idx = 0;

                for (idx = 0; idx < _profit_date.Length - 1; ++idx)
                {
                    double t = ((double)_profit_date[idx].Ticks + (double)_profit_date[idx + 1].Ticks) / 2;
                    if (x < t) break;
                }

                int xmin = 0;
                int xmax = _profit_price.Length;
                decimal yval = 0;
                if (idx > xmin && idx < xmax)
                {
                    switch (cbKind.SelectedIndex)
                    {
                        case 0: // profit
                        case 1: // profit
                        case 2: // profit
                            yval = _profit_price[idx];
                            break;
                        case 3: // drawdown
                            yval = _drawdown_price[idx];
                            break;
                    }
                    s = string.Format("{0:yyyy/MM/dd}: ${1:#,##0.##}", _profit_date[idx], yval);
                    System.Threading.Thread.Sleep(100);
                }
            }
            finally
            {
                reenter = 0;
            }
            return s;
        }

        private string surfProfitSimple_OnGetTipString(double x, double y)
        {
            return GetPlotTipString(x, y);
        }

        private void cbKind_SelectedIndexChanged(object sender, EventArgs e)
        {
            CreatePlot();
        }

        private void btnCopy_Click(object sender, EventArgs e)
        {
            surfProfitSimple.CopyToClipboard();
        }

        private void btnSave_Click(object sender, EventArgs e)
        {
            SaveFileDialog dlg = new SaveFileDialog();
            dlg.Filter = "PNG Files|*.png|All Files|*.*";
            if (dlg.ShowDialog() == DialogResult.OK)
            {
                surfProfitSimple.CopyToClipboard();
                var b = Clipboard.GetImage();
                b.Save(dlg.FileName);
            }
        }
    }
}
