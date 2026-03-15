namespace VisualPortfolio
{
    partial class FormPositionAnalysis
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code
        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            System.Windows.Forms.DataGridViewCellStyle dataGridViewCellStyle1 = new System.Windows.Forms.DataGridViewCellStyle();
            System.Windows.Forms.DataGridViewCellStyle dataGridViewCellStyle2 = new System.Windows.Forms.DataGridViewCellStyle();
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(FormPositionAnalysis));
            this.dvResultList = new System.Windows.Forms.DataGridView();
            this.contentMenuTabPage = new System.Windows.Forms.ContextMenuStrip(this.components);
            this.mtnSaveReport = new System.Windows.Forms.ToolStripMenuItem();
            this.tableLayoutPanel1 = new System.Windows.Forms.TableLayoutPanel();
            this.tableLayoutPanel2 = new System.Windows.Forms.TableLayoutPanel();
            this.btnBatchRun = new System.Windows.Forms.Button();
            this.btnReport = new System.Windows.Forms.Button();
            ((System.ComponentModel.ISupportInitialize)(this.dvResultList)).BeginInit();
            this.contentMenuTabPage.SuspendLayout();
            this.tableLayoutPanel1.SuspendLayout();
            this.tableLayoutPanel2.SuspendLayout();
            this.SuspendLayout();
            // 
            // dvResultList
            // 
            this.dvResultList.AllowUserToAddRows = false;
            this.dvResultList.AllowUserToDeleteRows = false;
            this.dvResultList.AllowUserToOrderColumns = true;
            this.dvResultList.AllowUserToResizeRows = false;
            this.dvResultList.AutoSizeColumnsMode = System.Windows.Forms.DataGridViewAutoSizeColumnsMode.AllCells;
            this.dvResultList.BackgroundColor = System.Drawing.Color.White;
            dataGridViewCellStyle1.Alignment = System.Windows.Forms.DataGridViewContentAlignment.MiddleLeft;
            dataGridViewCellStyle1.BackColor = System.Drawing.SystemColors.Control;
            dataGridViewCellStyle1.Font = new System.Drawing.Font("Microsoft Sans Serif", 8.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            dataGridViewCellStyle1.ForeColor = System.Drawing.SystemColors.WindowText;
            dataGridViewCellStyle1.SelectionBackColor = System.Drawing.SystemColors.Highlight;
            dataGridViewCellStyle1.SelectionForeColor = System.Drawing.SystemColors.HighlightText;
            dataGridViewCellStyle1.WrapMode = System.Windows.Forms.DataGridViewTriState.False;
            this.dvResultList.ColumnHeadersDefaultCellStyle = dataGridViewCellStyle1;
            this.dvResultList.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            this.dvResultList.ContextMenuStrip = this.contentMenuTabPage;
            dataGridViewCellStyle2.Alignment = System.Windows.Forms.DataGridViewContentAlignment.MiddleLeft;
            dataGridViewCellStyle2.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(192)))), ((int)(((byte)(255)))), ((int)(((byte)(192)))));
            dataGridViewCellStyle2.Font = new System.Drawing.Font("Microsoft Sans Serif", 8.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            dataGridViewCellStyle2.ForeColor = System.Drawing.SystemColors.ControlText;
            dataGridViewCellStyle2.SelectionBackColor = System.Drawing.Color.FromArgb(((int)(((byte)(192)))), ((int)(((byte)(255)))), ((int)(((byte)(192)))));
            dataGridViewCellStyle2.SelectionForeColor = System.Drawing.SystemColors.ControlText;
            dataGridViewCellStyle2.WrapMode = System.Windows.Forms.DataGridViewTriState.False;
            this.dvResultList.DefaultCellStyle = dataGridViewCellStyle2;
            this.dvResultList.Dock = System.Windows.Forms.DockStyle.Fill;
            this.dvResultList.GridColor = System.Drawing.Color.Gray;
            this.dvResultList.Location = new System.Drawing.Point(3, 38);
            this.dvResultList.Name = "dvResultList";
            this.dvResultList.Size = new System.Drawing.Size(583, 209);
            this.dvResultList.TabIndex = 1;
            this.dvResultList.TabStop = false;
            this.dvResultList.CellMouseClick += new System.Windows.Forms.DataGridViewCellMouseEventHandler(this.dvResultList_CellMouseClick);
            this.dvResultList.RowHeaderMouseDoubleClick += new System.Windows.Forms.DataGridViewCellMouseEventHandler(this.dvResultList_RowHeaderMouseDoubleClick);
            // 
            // contentMenuTabPage
            // 
            this.contentMenuTabPage.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.mtnSaveReport});
            this.contentMenuTabPage.Name = "contextMenuTabPage";
            this.contentMenuTabPage.Size = new System.Drawing.Size(125, 26);
            // 
            // mtnSaveReport
            // 
            this.mtnSaveReport.Name = "mtnSaveReport";
            this.mtnSaveReport.Size = new System.Drawing.Size(124, 22);
            this.mtnSaveReport.Text = "儲存報表";
            this.mtnSaveReport.Click += new System.EventHandler(this.mtnSaveReport_Click);
            // 
            // tableLayoutPanel1
            // 
            this.tableLayoutPanel1.ColumnCount = 1;
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableLayoutPanel1.Controls.Add(this.dvResultList, 0, 1);
            this.tableLayoutPanel1.Controls.Add(this.tableLayoutPanel2, 0, 0);
            this.tableLayoutPanel1.Dock = System.Windows.Forms.DockStyle.Fill;
            this.tableLayoutPanel1.Location = new System.Drawing.Point(0, 4);
            this.tableLayoutPanel1.Name = "tableLayoutPanel1";
            this.tableLayoutPanel1.RowCount = 2;
            this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle());
            this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableLayoutPanel1.Size = new System.Drawing.Size(589, 250);
            this.tableLayoutPanel1.TabIndex = 2;
            // 
            // tableLayoutPanel2
            // 
            this.tableLayoutPanel2.AutoSize = true;
            this.tableLayoutPanel2.AutoSizeMode = System.Windows.Forms.AutoSizeMode.GrowAndShrink;
            this.tableLayoutPanel2.ColumnCount = 3;
            this.tableLayoutPanel2.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel2.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel2.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableLayoutPanel2.Controls.Add(this.btnBatchRun, 0, 0);
            this.tableLayoutPanel2.Controls.Add(this.btnReport, 1, 0);
            this.tableLayoutPanel2.Dock = System.Windows.Forms.DockStyle.Fill;
            this.tableLayoutPanel2.Location = new System.Drawing.Point(3, 3);
            this.tableLayoutPanel2.Name = "tableLayoutPanel2";
            this.tableLayoutPanel2.RowCount = 1;
            this.tableLayoutPanel2.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableLayoutPanel2.Size = new System.Drawing.Size(583, 29);
            this.tableLayoutPanel2.TabIndex = 2;
            // 
            // btnBatchRun
            // 
            this.btnBatchRun.Location = new System.Drawing.Point(3, 3);
            this.btnBatchRun.Name = "btnBatchRun";
            this.btnBatchRun.Size = new System.Drawing.Size(75, 23);
            this.btnBatchRun.TabIndex = 0;
            this.btnBatchRun.Text = "批次分析";
            this.btnBatchRun.UseVisualStyleBackColor = true;
            this.btnBatchRun.Click += new System.EventHandler(this.btnBatchRun_Click);
            // 
            // btnReport
            // 
            this.btnReport.Location = new System.Drawing.Point(84, 3);
            this.btnReport.Name = "btnReport";
            this.btnReport.Size = new System.Drawing.Size(75, 23);
            this.btnReport.TabIndex = 1;
            this.btnReport.Text = "優化報表";
            this.btnReport.UseVisualStyleBackColor = true;
            this.btnReport.Click += new System.EventHandler(this.btnReport_Click);
            // 
            // FormPositionAnalysis
            // 
            this.ClientSize = new System.Drawing.Size(589, 254);
            this.CloseButton = false;
            this.CloseButtonVisible = false;
            this.Controls.Add(this.tableLayoutPanel1);
            this.Font = new System.Drawing.Font("Microsoft Sans Serif", 8.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Name = "FormPositionAnalysis";
            this.Padding = new System.Windows.Forms.Padding(0, 4, 0, 0);
            this.TabPageContextMenuStrip = this.contentMenuTabPage;
            this.Text = "口數分析";
            ((System.ComponentModel.ISupportInitialize)(this.dvResultList)).EndInit();
            this.contentMenuTabPage.ResumeLayout(false);
            this.tableLayoutPanel1.ResumeLayout(false);
            this.tableLayoutPanel1.PerformLayout();
            this.tableLayoutPanel2.ResumeLayout(false);
            this.ResumeLayout(false);

        }
        #endregion
        private System.Windows.Forms.DataGridView dvResultList;
        private System.Windows.Forms.ContextMenuStrip contentMenuTabPage;
        private System.Windows.Forms.ToolStripMenuItem mtnSaveReport;
        private System.Windows.Forms.TableLayoutPanel tableLayoutPanel1;
        private System.Windows.Forms.TableLayoutPanel tableLayoutPanel2;
        private System.Windows.Forms.Button btnBatchRun;
        private System.Windows.Forms.Button btnReport;
    }
}