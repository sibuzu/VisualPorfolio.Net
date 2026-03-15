using Microsoft.Reporting.WinForms;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Reflection;
using System.Windows.Forms;
using WeifenLuo.WinFormsUI.Docking;

namespace VisualPortfolio.Forms
{
    public partial class FormCommission : DockContent
    {
        public FormCommission()
        {
            InitializeComponent();
            reportCommission.LocalReport.SubreportProcessing += ReportCommission_SubreportProcessing;
        }

        private void ReportCommission_SubreportProcessing(object sender, SubreportProcessingEventArgs e)
        {
            string currentYear = e.Parameters["Year"].Values[0];

            var listYear = Global.CommissionSet.listYear;
            ClsCommissionYear yearData = listYear.FirstOrDefault(y => y.年度 == currentYear);

            if (yearData != null)
            {
                util.BindDataSource(e.DataSources, yearData.ListEntry, "DS_Entry");
            }
        }

        public void CreateCommissionResult()
        {
            try
            {
                Global.CommissionSet.BuildCommissionYears();

                util.BindDataSource(reportCommission, CreateConfigEntry(), "DS_Config");

                var listYear = Global.CommissionSet.listYear;
                util.BindDataSource(reportCommission, Global.CommissionSet.listYear, "DS_Year");
                this.reportCommission.RefreshReport();
            }
            catch (Exception e)
            {
                MessageBox.Show("CreateCommissionResult failed: " + e.Message);
            }
        }

        private List<TReportEntry> EmptyEntry()
        {
            return new List<TReportEntry>();
        }

        private List<TReportEntry> CreateConfigEntry()
        {
            List<TReportEntry> lst = new List<TReportEntry>();
            var cfg = Global.CommissionSet.cfg;
            bool skip = false;

            foreach (var property in cfg.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
            {
                var displayNameAttribute = property.GetCustomAttribute<DisplayNameAttribute>();

                if (displayNameAttribute != null)
                {
                    string displayName = displayNameAttribute.DisplayName;
                    string value = property.GetValue(cfg)?.ToString() ?? string.Empty;
                    if (property.Name.Contains("績效門檻")) skip = (value == "0");
                    if (property.Name.Contains("績效門檻") || property.Name.Contains("獎金比例"))
                    {
                        if (skip) continue;
                    }
                    lst.Add(new TReportEntry(displayName, value));
                }
            }

            return lst;
        }

        private void FormCommission_Load(object sender, EventArgs e)
        {

        }

        private void mtnConfig_Click(object sender, EventArgs e)
        {
            var cfg = Global.CommissionSet.cfg;
            try
            {
                var dlg = new DlgPropertyGrid();
                cfg.ChangePropertyVisibility();
                cfg.UIObject = dlg;
                dlg.Text = "Commisssion Config";
                dlg.SetReadOnly(false);
                dlg.SetSelectedObject(cfg);
                dlg.ShowDialog();
                CreateCommissionResult();
            }
            finally
            {
                cfg.UIObject = null;
            }
        }
    }
}
