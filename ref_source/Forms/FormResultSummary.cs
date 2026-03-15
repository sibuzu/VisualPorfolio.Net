using System;
using System.Windows.Forms;
using WeifenLuo.WinFormsUI.Docking;
using VisualPortfolio.Forms;

namespace VisualPortfolio
{
    public partial class FormResultSummary : DockContent
    {
        public bool SelectAll
        {
            get
            {
                return (dvResultList.Columns[0].HeaderCell as DGVColumnHeader).CheckAll;
            }
        }

        public FormResultSummary()
        {
            InitializeComponent();
        }

        internal void UpdateResultSummary()
        {
            Global.listResult.UpdateResult();
            dvResultList.DataSource = Global.listResult;
            dvResultList.Columns["獲利點"].DefaultCellStyle.Format = "0.##";
            dvResultList.Columns["MDD"].DefaultCellStyle.Format = "#,##0";
            dvResultList.Columns["PMR"].DefaultCellStyle.Format = "0.00";
            dvResultList.Columns["獲利"].DefaultCellStyle.Format = "#,##0";
            dvResultList.Columns["獲利比"].DefaultCellStyle.Format = "0.00%";
            dvResultList.Refresh();
        }

        private void mtnSaveReport_Click(object sender, EventArgs e)
        {
            // Create Strategy Executing Report
            SaveFileDialog dlg = new SaveFileDialog();

            // Set filter options and filter index.
            dlg.Filter = "Result Summary|*.csv|All Files|*.*";
            dlg.FilterIndex = 1;

            // Process input if the user clicked OK.
            if (dlg.ShowDialog() == DialogResult.OK)
            {
                // generate it
                util.ExportTable(dlg.FileName, dvResultList);
            }
        }
    }
}