using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using WeifenLuo.WinFormsUI.Docking;

namespace VisualPortfolio.Forms
{
    public partial class FormSimpleSummary : DockContent
    {
        public FormSimpleSummary()
        {
            InitializeComponent();
        }

        public void CreateSimpleSummary()
        {
            try
            {
                double factor = Global.listEquityAttr.ContractFactor;
                Global.SummaryReport.MddCount = Global.MddCount;
                Global.SummaryReport.CreateSimpleReport(Global.PortfolioList, factor);
                util.BindDataSource(reportSummary, Global.SummaryReport.GetReportList(Global.IDX_SUMMARY0), "DS_Summary1");
                util.BindDataSource(reportSummary, Global.SummaryReport.GetReportList(Global.IDX_SUMMARY1), "DS_Summary2");
                util.BindDataSource(reportSummary, Global.SummaryReport.GetReportList(Global.IDX_YEAR_PROFIT0), "DS_AnnualProfit1");
                util.BindDataSource(reportSummary, Global.SummaryReport.GetReportList(Global.IDX_YEAR_PROFIT1), "DS_AnnualProfit2");
                util.BindDataSource(reportSummary, Global.SummaryReport.GetReportList(Global.IDX_MONTH_PROFIT0), "DS_MonthProfit1");
                util.BindDataSource(reportSummary, Global.SummaryReport.GetReportList(Global.IDX_MONTH_PROFIT1), "DS_MonthProfit2");
                util.BindDataSource(reportSummary, Global.SummaryReport.GetReportList(Global.IDX_WEEK_PROFIT0), "DS_WeekProfit1");
                util.BindDataSource(reportSummary, Global.SummaryReport.GetReportList(Global.IDX_WEEK_PROFIT1), "DS_WeekProfit2");
                this.reportSummary.RefreshReport();
            }
            catch (Exception e)
            {
                MessageBox.Show("CreateSummaryReport failed: " + e.Message);
            }
        }

    }
}
