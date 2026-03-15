using System;
using System.Windows.Forms;
using WeifenLuo.WinFormsUI.Docking;
using VisualPortfolio.Forms;
using VisualPortfolio.Classes;
using System.Data;
using System.Collections.Generic;
using System.IO;
using System.Diagnostics;
using System.Text;

namespace VisualPortfolio
{
    public partial class FormPositionAnalysis : DockContent
    {
        private bool _selecting;

        public FormPositionAnalysis()
        {
            InitializeComponent();
            _selecting = false;
        }

        internal object[] CalcBatchResult(int idx, ClsBatchRunList p, List<int> indices)
        {
            List<object> r = new List<object>();
            r.Add(idx+1);

            decimal profit = 0;
            decimal dd = 0;
            decimal mdd = 0;    

            var dtStart = Global.frmEquityManage.GetRangeStart();
            var dtEnd = Global.frmEquityManage.GetRangeEnd();
            foreach (var ti in Global.RawPortfolioList)
            {
                if (ti.tradeDate2 < dtStart) continue;
                if (ti.tradeDate2 > dtEnd) break;
                int aux_count = p[ti.tag].Value;

                decimal px = ti.netProfit * aux_count * ti.aux_weight;
                profit += px;
                dd -= px;
                if (dd < 0) dd = 0;
                if (mdd < dd) mdd = dd;
            }

            decimal pmr = mdd == 0 ? 0 : profit / mdd;
            r.Add(profit);  // 獲利
            r.Add(mdd);  // MDD
            r.Add(pmr); // 獲利比

            for (int i = 0; i < indices.Count; ++i)
            {
                r.Add(p[indices[i]].Value);
            }

            return r.ToArray();
        }

        internal void UpdatePostionTable()
        {
            if (_selecting) return;

            ClsBatchRunList p = Global.listBatchRun;
            if (p.Count == 0) return;
            long n = p.GetCount();

            var data = new DataTable();
            data.Columns.Add("Index", typeof(Int32));
            data.Columns.Add("獲利", typeof(decimal));
            data.Columns.Add("MDD", typeof(decimal));
            data.Columns.Add("獲利/MDD", typeof(decimal));

            List<string> names = new List<string>();
            List<int> indices = new List<int>();
            for (int i = 0; i < p.Count; ++i)
            {
                if (p[i].Act && p[i].GetCount() > 1)
                {
                    data.Columns.Add(p[i].Name, typeof(Int32));
                    names.Add(p[i].Name);
                    indices.Add(i);
                }
            }

            for (int i = 0; i < n; i++)
            {
                p.GetParameters(i);
                data.Rows.Add(CalcBatchResult(i, p, indices));
            }

            dvResultList.DataSource = data;
            dvResultList.Columns[1].DefaultCellStyle.Format = "#,##0";
            dvResultList.Columns[2].DefaultCellStyle.Format = "#,##0";
            dvResultList.Columns[3].DefaultCellStyle.Format = "0.00";

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

        private void btnBatchRun_Click(object sender, EventArgs e)
        {
            var dlg = new FormBatchRun();
            if (dlg.ShowDialog() == DialogResult.OK)
            {
                UpdatePostionTable();
            }
        }

        private void dvResultList_RowHeaderMouseDoubleClick(object sender, DataGridViewCellMouseEventArgs e)
        {
        }

        private void dvResultList_CellMouseClick(object sender, DataGridViewCellMouseEventArgs e)
        {
            try
            {
                _selecting = true;

                ClsBatchRunList p = Global.listBatchRun;
                if (p.Count == 0) return;
                int idx = dvResultList.CurrentCell.RowIndex;
                int pidx = (int) dvResultList.Rows[idx].Cells[0].Value - 1;
                if (pidx >= 0 && pidx < p.GetCount())
                {
                    p.GetParameters(pidx);
                    for (int i = 0; i < p.Count; i++)
                    {
                        Global.listEquityAttr[i].Contract = p[i].Value;
                    }
                    Global.frmEquityManage.RefreshGrid();
                    Global.frmMain.UpdatePortfolio();
                    Global.frmMain.UpdateDraw();
                }
            }
            finally
            {
                _selecting = false;
            }
        }

        private void btnReport_Click(object sender, EventArgs e)
        {
            if (GenerateReport(Global.BatchResultFile))
            {
                OpenVisualTableFile(Global.BatchResultFile);
            }
        }

        private bool GenerateReport(string fname)
        {
            DataTable dt = dvResultList.DataSource as DataTable;
            if (dt == null || dt.Rows.Count == 0) return false;

            int ncol = dt.Columns.Count;
            int nrow = dt.Rows.Count;

            string header = "";
            string line = "";

            for (int i = 4; i < ncol; ++i)
            {
                header += dt.Columns[i].Caption + ",";
            }
            header += "Test,獲利,MDD,獲利/MDD";

            using (StreamWriter w = new StreamWriter(fname, false, Encoding.GetEncoding("BIG5")))
            {
                w.WriteLine(header);
                for (int k = 0; k < nrow; ++k)
                {
                    line = "";
                    for (int i = 4; i < ncol; ++i)
                    {
                        line += dt.Rows[k].ItemArray[i].ToString() + ",";
                    }
                    for (int i = 0; i < 4; ++i)
                    {
                        if (i > 0) line += ",";
                        line += dt.Rows[k].ItemArray[i].ToString();
                    }
                    w.WriteLine(line);
                }
            }

            return true;
        }

        private void OpenVisualTableFile(string filename)
        {
            if (!File.Exists(Global.VisualTableExe))
            {
                MessageBox.Show(string.Format("Cannot find {0}.  Please open {1} manually.",
                    Global.VisualTableExe, filename));
                return;
            }

            // Configure the process using the StartInfo properties.
            Process process = new Process();
            process.StartInfo.FileName = Global.VisualTableExe;
            process.StartInfo.Arguments = "\"" + filename + "\"";
            process.Start();
        }
    }
}