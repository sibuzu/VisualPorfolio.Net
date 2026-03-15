using System;
using System.Windows.Forms;
using WeifenLuo.WinFormsUI.Docking;
using VisualPortfolio.Forms;
using System.Collections.Generic;
using VisualPortfolio.Classes;

namespace VisualPortfolio
{
    public partial class FormWinLoss : DockContent
    {
        public bool SelectAll
        {
            get
            {
                return (dvResultList.Columns[0].HeaderCell as DGVColumnHeader).CheckAll;
            }
        }

        public FormWinLoss()
        {
            InitializeComponent();
        }

        internal void UpdateWinLossTable()
        {
            var winlost = Global.listWinLoss;
            var lst = new List<ClsWinLossRow>();
            ClsWinLossRow row;

            // 總次數
            row = new ClsWinLossRow();
            row.項目 = "總次數";
            row.日 = winlost.Items[0].總次數.ToString();
            row.週 = winlost.Items[1].總次數.ToString();
            row.月 = winlost.Items[2].總次數.ToString();
            row.年 = winlost.Items[3].總次數.ToString();
            lst.Add(row);

            // 贏錢次數
            row = new ClsWinLossRow();
            row.項目 = "贏錢次數";
            row.日 = winlost.Items[0].贏錢次數.ToString();
            row.週 = winlost.Items[1].贏錢次數.ToString();
            row.月 = winlost.Items[2].贏錢次數.ToString();
            row.年 = winlost.Items[3].贏錢次數.ToString();
            lst.Add(row);

            // 輸錢次數
            row = new ClsWinLossRow();
            row.項目 = "輸錢次數";
            row.日 = winlost.Items[0].輸錢次數.ToString();
            row.週 = winlost.Items[1].輸錢次數.ToString();
            row.月 = winlost.Items[2].輸錢次數.ToString();
            row.年 = winlost.Items[3].輸錢次數.ToString();
            lst.Add(row);

            // 贏錢機率
            row = new ClsWinLossRow();
            row.項目 = "贏錢機率";
            row.日 = winlost.Items[0].贏錢機率.ToString("0.00%");
            row.週 = winlost.Items[1].贏錢機率.ToString("0.00%");
            row.月 = winlost.Items[2].贏錢機率.ToString("0.00%");
            row.年 = winlost.Items[3].贏錢機率.ToString("0.00%");
            lst.Add(row);

            // 平均每次贏錢
            row = new ClsWinLossRow();
            row.項目 = "平均每次贏錢";
            row.日 = winlost.Items[0].平均每次贏錢.ToString("#,##0");
            row.週 = winlost.Items[1].平均每次贏錢.ToString("#,##0");
            row.月 = winlost.Items[2].平均每次贏錢.ToString("#,##0");
            row.年 = winlost.Items[3].平均每次贏錢.ToString("#,##0");
            lst.Add(row);

            // 平均每次輸錢
            row = new ClsWinLossRow();
            row.項目 = "平均每次輸錢";
            row.日 = winlost.Items[0].平均每次輸錢.ToString("#,##0");
            row.週 = winlost.Items[1].平均每次輸錢.ToString("#,##0");
            row.月 = winlost.Items[2].平均每次輸錢.ToString("#,##0");
            row.年 = winlost.Items[3].平均每次輸錢.ToString("#,##0");
            lst.Add(row);

            // 最大贏錢
            row = new ClsWinLossRow();
            row.項目 = "最大贏錢";
            row.日 = winlost.Items[0].最大贏錢.ToString("#,##0");
            row.週 = winlost.Items[1].最大贏錢.ToString("#,##0");
            row.月 = winlost.Items[2].最大贏錢.ToString("#,##0");
            row.年 = winlost.Items[3].最大贏錢.ToString("#,##0");
            lst.Add(row);

            // 最大輸錢
            row = new ClsWinLossRow();
            row.項目 = "最大輸錢";
            row.日 = winlost.Items[0].最大輸錢.ToString("#,##0");
            row.週 = winlost.Items[1].最大輸錢.ToString("#,##0");
            row.月 = winlost.Items[2].最大輸錢.ToString("#,##0");
            row.年 = winlost.Items[3].最大輸錢.ToString("#,##0");
            lst.Add(row);

            // 平均每次贏錢
            row = new ClsWinLossRow();
            row.項目 = "每次贏輸比";
            row.日 = winlost.Items[0].每次贏輸比.ToString("0.00");
            row.週 = winlost.Items[1].每次贏輸比.ToString("0.00");
            row.月 = winlost.Items[2].每次贏輸比.ToString("0.00");
            row.年 = winlost.Items[3].每次贏輸比.ToString("0.00");
            lst.Add(row);

            // 全部贏輸比
            row = new ClsWinLossRow();
            row.項目 = "全部贏輸比";
            row.日 = winlost.Items[0].全部贏輸比.ToString("0.00");
            row.週 = winlost.Items[1].全部贏輸比.ToString("0.00");
            row.月 = winlost.Items[2].全部贏輸比.ToString("0.00");
            row.年 = winlost.Items[3].全部贏輸比.ToString("0.00");
            lst.Add(row);

            dvResultList.DataSource = lst;
            dvResultList.Columns[1].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
            dvResultList.Columns[2].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
            dvResultList.Columns[3].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
            dvResultList.Columns[4].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
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