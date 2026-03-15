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
    public partial class FormEquityManage : DockContent
    {
        public bool SelectAll
        {
            get
            {
                return (dvEquityList.Columns["Active"].HeaderCell as DGVColumnHeader).CheckAll;
            }
        }

        internal bool SuspendUpdate;

        public FormEquityManage()
        {
            this.SuspendUpdate = false;

            InitializeComponent();

            dvEquityList.DataSource = Global.listEquityAttr;

            DataGridViewButtonColumn btn = new DataGridViewButtonColumn();
            btn.FlatStyle = FlatStyle.Popup;
            btn.HeaderText = "顏色";
            btn.Name = "Color";
            btn.Text = "";
            btn.Width = 40;
            btn.UseColumnTextForButtonValue = true;
            dvEquityList.Columns.Insert(2, btn);

            btn = new DataGridViewButtonColumn();
            btn.FlatStyle = FlatStyle.Popup;
            btn.HeaderText = "";
            btn.Name = "Edit";
            btn.Text = "...";
            btn.Width = dvEquityList.RowTemplate.Height;
            btn.UseColumnTextForButtonValue = true;
            dvEquityList.Columns.Add(btn);

            btn = new DataGridViewButtonColumn();
            btn.FlatStyle = FlatStyle.Popup;
            btn.HeaderText = "";
            btn.Name = "Delete";
            btn.Text = "X";
            btn.ToolTipText = "";
            btn.Width = dvEquityList.RowTemplate.Height;
            btn.UseColumnTextForButtonValue = true;
            dvEquityList.Columns.Add(btn);

            DataGridViewColumnCollection dcc = dvEquityList.Columns;
            dcc["Active"].Width = 25;
            dcc["Index"].Width = 30;
            dcc["Contract"].Width = 40;
            dcc["Weight"].Width = 40;
            dcc["BaseFileName"].Width = 80;
            dcc["名稱"].Width = 80;

            dvEquityList.Columns[0].HeaderCell = new DGVColumnHeader();
        }

        private void dvEquityList_CellValueChanged(object sender, DataGridViewCellEventArgs e)
        {
            if (!this.SuspendUpdate)
            {
                Global.frmMain.UpdatePortfolio();
                Global.frmMain.UpdateDraw();
            }
        }

        private void dvEquityList_CellContentClick(object sender, DataGridViewCellEventArgs e)
        {
            var gv = sender as DataGridView;
            var col = gv.Columns[e.ColumnIndex];

            if (gv.RowCount == 0) return;

            if (col.Name == "Color" && e.RowIndex >= 0)
            {
                gv.CurrentCell.Selected = false;
                SetColorButton(e.RowIndex, gv.CurrentCell as DataGridViewButtonCell);
            }
            else if (col.Name == "Edit" && e.RowIndex >= 0)
            {
                EditButton(e.RowIndex);
            }
            else if (col.Name == "Delete" && e.RowIndex >= 0)
            {
                RemoveButton(e.RowIndex);
            }
            else if (col.Name == "Active" && e.RowIndex >= 0)
            {
                gv.CommitEdit(DataGridViewDataErrorContexts.Commit);
            }
            else
            {
                gv.BeginEdit(true);
            }
        }

        private void SetColorButton(int idx, DataGridViewButtonCell btn)
        {
            if (idx < 0 || idx >= Global.listEquityAttr.Count) return;
            ClsEquityAttr ea = Global.listEquityAttr[idx];

            ColorDialog dlg = new ColorDialog();
            dlg.Color = ea.Color;

            if (dlg.ShowDialog() == DialogResult.OK)
            {
                ea.Color = dlg.Color;
                btn.Style.BackColor = ea.Color;
                btn.Style.SelectionBackColor = ea.Color;
            }

            // UpdateDraw();
        }

        private void RemoveButton(int idx)
        {
            if (idx < 0 || idx >= Global.listEquityAttr.Count) return;

            Global.listEquityAttr.RemoveEntry(idx);
            dvEquityList.Refresh();
            Global.frmMain.UpdatePortfolio();
            Global.frmMain.UpdateDraw();
        }

        private void EditButton(int idx)
        {
            if (idx < 0 || idx >= Global.listEquityAttr.Count) return;
            ClsEquityAttr ea = Global.listEquityAttr[idx];

            OpenFileDialog dlg = new OpenFileDialog();
            dlg.FileName = ea.FileName;
            dlg.Filter = "Report Files|*.xml;*.srp;*.xrp|All Files|*.*";
            dlg.FilterIndex = 1;
            dlg.Multiselect = false;

            if (dlg.ShowDialog() == DialogResult.OK)
            {
                ea.FileName = dlg.FileName;
                ea.TradeList.LoadFile(ea.FileName);

                dvEquityList.Invalidate();
                Global.frmMain.UpdatePortfolio();
                Global.frmMain.UpdateDraw();
            }
        }

        private void dvEquityList_ColumnHeaderMouseClick(object sender, DataGridViewCellMouseEventArgs e)
        {
            var gv = sender as DataGridView;
            var col = gv.Columns[e.ColumnIndex];

            if (col is DataGridViewCheckBoxColumn)
            {
                try
                {
                    this.SuspendUpdate = true;

                    gv.EndEdit();
                    if (gv.RowCount > 0) gv.CurrentCell = gv.Rows[0].Cells["Index"];

                    gv.SuspendLayout();
                    foreach (DataGridViewRow row in gv.Rows)
                    {
                        row.Cells[e.ColumnIndex].Value = SelectAll;
                    }
                    gv.ResumeLayout();

                    Global.frmMain.UpdatePortfolio();
                    Global.frmMain.UpdateDraw();
                }
                finally
                {
                    this.SuspendUpdate = false;
                }
            }
        }

        internal void UpdateButtonColor()
        {
            foreach (DataGridViewRow row in dvEquityList.Rows)
            {
                DataGridViewButtonCell btn = (row.Cells["Color"] as DataGridViewButtonCell);
                btn.Style.BackColor = Global.listEquityAttr[btn.RowIndex].Color;
                btn.Style.SelectionBackColor = btn.Style.BackColor;
            }
            // dvEquityList.Refresh();
        }

        internal void RefreshGrid()
        {
            dvEquityList.Refresh();
        }

        internal static Color GetDefaultColor(int idx)
        {
            Color[] List = { Color.Blue, Color.Orange, Color.Maroon, Color.Cyan, Color.Green,
                Color.Fuchsia, Color.Olive, Color.Purple, Color.LimeGreen, Color.Salmon };

            if (idx < 0) return Color.Red;
            return List[idx % List.Length];
        }

        private void btnAdd_Click(object sender, EventArgs e)
        {
            OpenFileDialog dlg = new OpenFileDialog();
            dlg.Filter = "Report Files|*.xml;*.srp;*.xrp|All Files|*.*";
            dlg.FilterIndex = 1;
            dlg.Multiselect = true;

            if (dlg.ShowDialog() == DialogResult.OK)
            {
                try
                {
                    Application.UseWaitCursor = true;

                    int idx = dvEquityList.RowCount;
                    foreach (string fname in dlg.FileNames)
                    {
                        var ea = new ClsEquityAttr();
                        ea.FileName = fname;
                        ea.Index = idx++;
                        ea.Color = GetDefaultColor(ea.Index);
                        ea.Active = true;
                        ea.Contract = 1;
                        ea.Weight = 1;
                        ea.TradeList.LoadFile(ea.FileName);
                        Global.listEquityAttr.Add(ea);
                    }

                    Global.listEquityAttr.ResetIndex();
                    UpdateButtonColor();
                    dvEquityList.Invalidate();

                    Global.frmMain.UpdatePortfolio();
                    Global.frmMain.UpdateDraw();
                }
                finally
                {
                    Application.UseWaitCursor = false;
                }
            }
        }

        private void btnMoveUp_Click(object sender, EventArgs e)
        {
            if (dvEquityList.CurrentCell == null) return;
            int idx = Global.listEquityAttr.MoveUp(dvEquityList.CurrentCell.RowIndex);

            dvEquityList.CurrentCell = dvEquityList.Rows[idx].Cells[0];
            UpdateButtonColor();
            dvEquityList.Invalidate();
        }

        private void btnMoveDown_Click(object sender, EventArgs e)
        {
            if (dvEquityList.CurrentCell == null) return;
            int idx = Global.listEquityAttr.MoveDown(dvEquityList.CurrentCell.RowIndex);

            dvEquityList.CurrentCell = dvEquityList.Rows[idx].Cells[0];
            UpdateButtonColor();
            dvEquityList.Invalidate();
        }

        private void chkDivByCount_CheckedChanged(object sender, EventArgs e)
        {
            Global.listEquityAttr.DivByCount = (sender as CheckBox).Checked;
            Global.frmMain.UpdatePortfolio();
            Global.frmMain.UpdateDraw();
        }

        private void chkRangeAll_CheckedChanged(object sender, EventArgs e)
        {
            bool chk = (sender as CheckBox).Checked;
            dtRangeStart.Enabled = !chk;
            dtRangeEnd.Enabled = !chk;
            Global.frmMain.UpdatePortfolio();
            Global.frmMain.UpdateDraw();
        }

        private void dtRange_ValueChanged(object sender, EventArgs e)
        {
            Global.frmMain.UpdatePortfolio();
            Global.frmMain.UpdateDraw();
        }

        internal void UpdateRangePicker()
        {
            var plist = Global.RawPortfolioList;
            if (chkRangeAll.Checked && plist.Count > 0)
            {
                dtRangeStart.Value = plist[0].tradeDate2;
                dtRangeEnd.Value = plist[plist.Count - 1].tradeDate2;
            }
        }

        internal DateTime GetRangeStart()
        {
            return chkRangeAll.Checked ? new DateTime(1900, 1, 1) : dtRangeStart.Value;
        }

        internal DateTime GetRangeEnd()
        {
            return chkRangeAll.Checked ? new DateTime(2100, 1, 1) : dtRangeEnd.Value;
        }

        private void btnFixProfit_Click(object sender, EventArgs e)
        {
            DateTime start = new DateTime(2020, 1, 1);
            DateTime end = new DateTime(2025, 5, 31);


            var plist = Global.RawPortfolioList;
            if (plist.Count >0)
            {
                start = plist[0].tradeDate2;
                end = plist[plist.Count - 1].tradeDate2;
            }

            var dlg = new DlgFixProfit();
            dlg.start = start;
            dlg.end = end;

            if (dlg.ShowDialog() != DialogResult.Yes) return;

            try
            {
                Application.UseWaitCursor = true;

                int idx = dvEquityList.RowCount + 1;
                var ea = ClsEquityAttr.CreateFixProfit(dlg.start, dlg.end, dlg.profit, idx, GetDefaultColor(idx));
                Global.listEquityAttr.Add(ea);
                Global.listEquityAttr.ResetIndex();
                UpdateButtonColor();
                dvEquityList.Invalidate();

                Global.frmMain.UpdatePortfolio();
                Global.frmMain.UpdateDraw();
            }
            finally
            {
                Application.UseWaitCursor = false;
            }
        }
    }

    public class DGVColumnHeader : DataGridViewColumnHeaderCell
    {

        private Rectangle CheckBoxRegion;
        private bool checkAll = true;

        protected override void Paint(Graphics graphics,
            Rectangle clipBounds, Rectangle cellBounds, int rowIndex,
            DataGridViewElementStates dataGridViewElementState,
            object value, object formattedValue, string errorText,
            DataGridViewCellStyle cellStyle, DataGridViewAdvancedBorderStyle advancedBorderStyle,
            DataGridViewPaintParts paintParts)
        {

            base.Paint(graphics, clipBounds, cellBounds, rowIndex, dataGridViewElementState, value,
                formattedValue, errorText, cellStyle, advancedBorderStyle, paintParts);

            graphics.FillRectangle(new SolidBrush(cellStyle.BackColor), cellBounds);

            CheckBoxRegion = new Rectangle(
                cellBounds.Location.X + 2,
                cellBounds.Location.Y + 3,
                25, cellBounds.Size.Height - 6);


            if (this.checkAll)
                ControlPaint.DrawCheckBox(graphics, CheckBoxRegion, ButtonState.Checked);
            else
                ControlPaint.DrawCheckBox(graphics, CheckBoxRegion, ButtonState.Normal);
        }

        protected override void OnMouseClick(DataGridViewCellMouseEventArgs e)
        {
            //Convert the CheckBoxRegion 
            Rectangle rec = new Rectangle(new Point(0, 0), this.CheckBoxRegion.Size);
            this.checkAll = !this.checkAll;
            if (rec.Contains(e.Location))
            {
                this.DataGridView.Invalidate();
            }
            base.OnMouseClick(e);
        }

        public bool CheckAll
        {
            get { return this.checkAll; }
            set { this.checkAll = value; }
        }
    }
}
