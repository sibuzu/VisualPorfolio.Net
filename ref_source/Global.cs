using VisualPortfolio.Forms;
using System.Collections.Generic;
using VisualPortfolio.Classes;
using System.IO;
using System.Windows.Forms;
using System;

namespace VisualPortfolio
{
    class Global
    {
        static internal FormMain frmMain;
        static internal TSummaryReport SummaryReport;

        // static internal List<ClsTradeListEx> TradeList;
        static internal List<ClsTradeItem> RawPortfolioList;
        static internal List<ClsTradeItem> PortfolioList;
        static internal ClsWinLossList listWinLoss;
        static internal ClsListEquity listEquityAttr;
        static internal ClsExecResultList listResult;
        static internal ClsBatchRunList listBatchRun;
        static internal ClsCommissionSet CommissionSet = new ClsCommissionSet();

        static internal FormSimpleSummary frmSimpleSummary;
        static internal FormSimplePlot frmSimplePlot;
        static internal FormSimpleMonth frmSimpleMonth;
        static internal FormEquityManage frmEquityManage;
        static internal FormPositionAnalysis frmPositionAnalysis;
        static internal FormResultSummary frmResultSummary;
        static internal FormWinLoss frmWinLoss;
        static internal FormCommission frmCommission;
        static internal FormDiversity frmDiversity;

        static internal decimal Slippage = 0;
        static internal decimal MinPointUnit = 1;
        static internal decimal MinPointPrice = 200;
        static internal decimal TotalMDD = 0;

        static internal string PlotTitle = "";
        static internal int MddCount = 5;
        static internal double Capital = 100;
        static internal double RiskFreeRate = 3;
        static internal bool 計算每日DD = false;

        internal static void AddInfo(string msg)
        {
            MessageBox.Show(msg);
        }

        static internal string DockPanelFile = "PorfilioPanel.xml";

        public const int IDX_SUMMARY0 = 0;
        public const int IDX_SUMMARY1 = 1;
        public const int IDX_YEAR_PROFIT0 = 2;
        public const int IDX_YEAR_PROFIT1 = 3;
        public const int IDX_MONTH_PROFIT0 = 4;
        public const int IDX_MONTH_PROFIT1 = 5;
        public const int IDX_WEEK_PROFIT0 = 6;
        public const int IDX_WEEK_PROFIT1 = 7;

        static internal string GetPlotTitle()
        {
            return Global.PlotTitle;
        }

        internal static string AppPath
        {
            get
            {
                return Path.GetDirectoryName(Application.ExecutablePath);
            }
        }

        public static string BatchResultFile
        {
            get
            {
                return Path.Combine(Global.AppPath, "BacktestResults.csv");
            }
        }

        public static string VisualTableExe
        {
            get
            {
                return Path.Combine(AppPath, "VisualTable.exe");
            }
        }
    }
}
