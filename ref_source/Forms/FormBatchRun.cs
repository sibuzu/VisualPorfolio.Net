using VisualPortfolio.Classes;
using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using System.Linq;

namespace VisualPortfolio.Forms
{
    public partial class FormBatchRun : Form
    {
        private ClsBatchRunList _runParameters;

        public FormBatchRun()
        {
            InitializeComponent();
            AssignListFromGlobal();
        }

        private void CellFormatting(int RowIndex, int ColumnIndex)
        {
            Color c;
            ClsBatchRunList p = _runParameters;
            if (p != null && RowIndex < p.Count)
            {
                bool act = p[RowIndex].Act;
                switch (ColumnIndex)
                {
                    case 2:
                        c = act ? Color.LightGray : Color.Black;
                        break;
                    case 3:
                    case 4:
                    case 5:
                        c = act ? Color.Black : Color.LightGray;
                        break;
                    default:
                        c = Color.Black;
                        break;
                }

                // for 回測商品
                if (RowIndex == 0 && ColumnIndex>=2) c = Color.LightGray;

                dvBatchRun.Rows[RowIndex].Cells[ColumnIndex].Style =
                      new DataGridViewCellStyle { ForeColor = c };
            }
        }

        private void dvBatchRun_CellFormatting(object sender, DataGridViewCellFormattingEventArgs e)
        {
            CellFormatting(e.RowIndex, e.ColumnIndex);
        }

        private void dvBatchRun_CellClick(object sender, DataGridViewCellEventArgs e)
        {
            if (e.ColumnIndex == 0)
            {
                ClsBatchRunList p = _runParameters;
                if (p != null && e.RowIndex < p.Count)
                {
                    dvBatchRun.EndEdit();
                    p[e.RowIndex].Act = !p[e.RowIndex].Act;
                    dvBatchRun.Invalidate();
                }
            }
        }

        private void btnBacktestRun_Click(object sender, EventArgs e)
        {
            AssignListToGlobal();
            DialogResult = DialogResult.OK;
        }

        private bool ValidateParameter()
        {
            int count = 0;
            foreach (var br in _runParameters)
            {
                if (br.Act) count++;
            }

            if (count < 1)
            {
                MessageBox.Show("批次參數要在1個以上");
                return false;
            }

            return true;
        }

        private void AssignListToGlobal()
        {
            Global.listBatchRun.Clear();
            foreach (var br in _runParameters)
                Global.listBatchRun.Add(br);
        }

        private void AssignListFromGlobal()
        {
            _runParameters = new ClsBatchRunList();
            foreach (var ea in Global.listEquityAttr)
            {
                ClsBatchRun br = new ClsBatchRun();
                br.No = ea.Index;
                br.Name = ea.GetName();
                br.Value = ea.Contract;

                var br2 = Global.listBatchRun.FirstOrDefault(x => x.Name == br.Name);
                if (br2!=null)
                {
                    br.Act = br2.Act;
                    br.Start = br2.Start;
                    br.Step = br2.Step;
                    br.End = br2.End;
                }
                else
                {
                    br.Act = false;
                    br.Start = 1;
                    br.Step = 1;
                    br.End = Math.Max(10, br.Value);
                }

                _runParameters.Add(br);
            }

            // assign to grid
            dvBatchRun.DataSource = _runParameters;
            dvBatchRun.Columns[0].Width = 30;
            dvBatchRun.Columns[1].Width = 30;
            dvBatchRun.Columns[2].Width = 120;
            dvBatchRun.Columns[3].Width = 40;
            dvBatchRun.Columns[4].Width = 40;
            dvBatchRun.Columns[5].Width = 40;
            dvBatchRun.Columns[6].Width = 40;
        }
    }
}
