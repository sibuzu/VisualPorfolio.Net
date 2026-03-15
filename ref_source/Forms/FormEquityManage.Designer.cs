namespace VisualPortfolio.Forms
{
    partial class FormEquityManage
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
            System.Windows.Forms.DataGridViewCellStyle dataGridViewCellStyle1 = new System.Windows.Forms.DataGridViewCellStyle();
            System.Windows.Forms.DataGridViewCellStyle dataGridViewCellStyle2 = new System.Windows.Forms.DataGridViewCellStyle();
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(FormEquityManage));
            this.tableLayoutPanel1 = new System.Windows.Forms.TableLayoutPanel();
            this.dvEquityList = new System.Windows.Forms.DataGridView();
            this.tableLayoutPanel2 = new System.Windows.Forms.TableLayoutPanel();
            this.btnFixProfit = new System.Windows.Forms.Button();
            this.btnMoveDown = new System.Windows.Forms.Button();
            this.btnMoveUp = new System.Windows.Forms.Button();
            this.chkDivByCount = new System.Windows.Forms.CheckBox();
            this.btnAdd = new System.Windows.Forms.Button();
            this.tableLayoutPanel3 = new System.Windows.Forms.TableLayoutPanel();
            this.chkRangeAll = new System.Windows.Forms.CheckBox();
            this.label1 = new System.Windows.Forms.Label();
            this.dtRangeStart = new System.Windows.Forms.DateTimePicker();
            this.dtRangeEnd = new System.Windows.Forms.DateTimePicker();
            this.label2 = new System.Windows.Forms.Label();
            this.label3 = new System.Windows.Forms.Label();
            this.tableLayoutPanel1.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dvEquityList)).BeginInit();
            this.tableLayoutPanel2.SuspendLayout();
            this.tableLayoutPanel3.SuspendLayout();
            this.SuspendLayout();
            // 
            // tableLayoutPanel1
            // 
            this.tableLayoutPanel1.ColumnCount = 1;
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableLayoutPanel1.Controls.Add(this.dvEquityList, 0, 2);
            this.tableLayoutPanel1.Controls.Add(this.tableLayoutPanel2, 0, 1);
            this.tableLayoutPanel1.Controls.Add(this.tableLayoutPanel3, 0, 0);
            this.tableLayoutPanel1.Dock = System.Windows.Forms.DockStyle.Fill;
            this.tableLayoutPanel1.Location = new System.Drawing.Point(0, 0);
            this.tableLayoutPanel1.Name = "tableLayoutPanel1";
            this.tableLayoutPanel1.RowCount = 3;
            this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle());
            this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle());
            this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableLayoutPanel1.Size = new System.Drawing.Size(371, 321);
            this.tableLayoutPanel1.TabIndex = 0;
            // 
            // dvEquityList
            // 
            this.dvEquityList.AllowUserToAddRows = false;
            this.dvEquityList.AllowUserToDeleteRows = false;
            this.dvEquityList.AllowUserToResizeRows = false;
            this.dvEquityList.BackgroundColor = System.Drawing.Color.White;
            dataGridViewCellStyle1.Alignment = System.Windows.Forms.DataGridViewContentAlignment.MiddleLeft;
            dataGridViewCellStyle1.BackColor = System.Drawing.SystemColors.Control;
            dataGridViewCellStyle1.Font = new System.Drawing.Font("Microsoft Sans Serif", 8.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            dataGridViewCellStyle1.ForeColor = System.Drawing.SystemColors.WindowText;
            dataGridViewCellStyle1.SelectionBackColor = System.Drawing.SystemColors.Highlight;
            dataGridViewCellStyle1.SelectionForeColor = System.Drawing.SystemColors.HighlightText;
            dataGridViewCellStyle1.WrapMode = System.Windows.Forms.DataGridViewTriState.False;
            this.dvEquityList.ColumnHeadersDefaultCellStyle = dataGridViewCellStyle1;
            this.dvEquityList.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            dataGridViewCellStyle2.Alignment = System.Windows.Forms.DataGridViewContentAlignment.MiddleLeft;
            dataGridViewCellStyle2.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(192)))), ((int)(((byte)(255)))), ((int)(((byte)(192)))));
            dataGridViewCellStyle2.Font = new System.Drawing.Font("Microsoft Sans Serif", 8.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            dataGridViewCellStyle2.ForeColor = System.Drawing.SystemColors.ControlText;
            dataGridViewCellStyle2.SelectionBackColor = System.Drawing.Color.FromArgb(((int)(((byte)(192)))), ((int)(((byte)(255)))), ((int)(((byte)(192)))));
            dataGridViewCellStyle2.SelectionForeColor = System.Drawing.SystemColors.ControlText;
            dataGridViewCellStyle2.WrapMode = System.Windows.Forms.DataGridViewTriState.False;
            this.dvEquityList.DefaultCellStyle = dataGridViewCellStyle2;
            this.dvEquityList.Dock = System.Windows.Forms.DockStyle.Fill;
            this.dvEquityList.EditMode = System.Windows.Forms.DataGridViewEditMode.EditOnEnter;
            this.dvEquityList.GridColor = System.Drawing.Color.Gray;
            this.dvEquityList.Location = new System.Drawing.Point(3, 57);
            this.dvEquityList.MultiSelect = false;
            this.dvEquityList.Name = "dvEquityList";
            this.dvEquityList.RowHeadersWidth = 25;
            this.dvEquityList.ShowCellToolTips = false;
            this.dvEquityList.Size = new System.Drawing.Size(365, 261);
            this.dvEquityList.TabIndex = 50;
            this.dvEquityList.CellContentClick += new System.Windows.Forms.DataGridViewCellEventHandler(this.dvEquityList_CellContentClick);
            this.dvEquityList.CellValueChanged += new System.Windows.Forms.DataGridViewCellEventHandler(this.dvEquityList_CellValueChanged);
            this.dvEquityList.ColumnHeaderMouseClick += new System.Windows.Forms.DataGridViewCellMouseEventHandler(this.dvEquityList_ColumnHeaderMouseClick);
            // 
            // tableLayoutPanel2
            // 
            this.tableLayoutPanel2.AutoSize = true;
            this.tableLayoutPanel2.AutoSizeMode = System.Windows.Forms.AutoSizeMode.GrowAndShrink;
            this.tableLayoutPanel2.ColumnCount = 5;
            this.tableLayoutPanel2.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel2.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel2.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel2.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel2.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel2.Controls.Add(this.btnFixProfit, 3, 0);
            this.tableLayoutPanel2.Controls.Add(this.btnMoveDown, 2, 0);
            this.tableLayoutPanel2.Controls.Add(this.btnMoveUp, 1, 0);
            this.tableLayoutPanel2.Controls.Add(this.chkDivByCount, 4, 0);
            this.tableLayoutPanel2.Controls.Add(this.btnAdd, 0, 0);
            this.tableLayoutPanel2.Dock = System.Windows.Forms.DockStyle.Fill;
            this.tableLayoutPanel2.Location = new System.Drawing.Point(3, 28);
            this.tableLayoutPanel2.Name = "tableLayoutPanel2";
            this.tableLayoutPanel2.RowCount = 1;
            this.tableLayoutPanel2.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableLayoutPanel2.Size = new System.Drawing.Size(365, 23);
            this.tableLayoutPanel2.TabIndex = 51;
            // 
            // btnFixProfit
            // 
            this.btnFixProfit.BackgroundImage = ((System.Drawing.Image)(resources.GetObject("btnFixProfit.BackgroundImage")));
            this.btnFixProfit.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Stretch;
            this.btnFixProfit.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnFixProfit.Location = new System.Drawing.Point(72, 0);
            this.btnFixProfit.Margin = new System.Windows.Forms.Padding(0, 0, 1, 0);
            this.btnFixProfit.Name = "btnFixProfit";
            this.btnFixProfit.Size = new System.Drawing.Size(23, 23);
            this.btnFixProfit.TabIndex = 41;
            this.btnFixProfit.UseVisualStyleBackColor = true;
            this.btnFixProfit.Click += new System.EventHandler(this.btnFixProfit_Click);
            // 
            // btnMoveDown
            // 
            this.btnMoveDown.BackgroundImage = ((System.Drawing.Image)(resources.GetObject("btnMoveDown.BackgroundImage")));
            this.btnMoveDown.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Center;
            this.btnMoveDown.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnMoveDown.Location = new System.Drawing.Point(48, 0);
            this.btnMoveDown.Margin = new System.Windows.Forms.Padding(0, 0, 1, 0);
            this.btnMoveDown.Name = "btnMoveDown";
            this.btnMoveDown.Size = new System.Drawing.Size(23, 23);
            this.btnMoveDown.TabIndex = 40;
            this.btnMoveDown.UseVisualStyleBackColor = true;
            this.btnMoveDown.Click += new System.EventHandler(this.btnMoveDown_Click);
            // 
            // btnMoveUp
            // 
            this.btnMoveUp.BackgroundImage = ((System.Drawing.Image)(resources.GetObject("btnMoveUp.BackgroundImage")));
            this.btnMoveUp.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Center;
            this.btnMoveUp.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnMoveUp.Location = new System.Drawing.Point(24, 0);
            this.btnMoveUp.Margin = new System.Windows.Forms.Padding(0, 0, 1, 0);
            this.btnMoveUp.Name = "btnMoveUp";
            this.btnMoveUp.Size = new System.Drawing.Size(23, 23);
            this.btnMoveUp.TabIndex = 39;
            this.btnMoveUp.UseVisualStyleBackColor = true;
            this.btnMoveUp.Click += new System.EventHandler(this.btnMoveUp_Click);
            // 
            // chkDivByCount
            // 
            this.chkDivByCount.AutoSize = true;
            this.chkDivByCount.Dock = System.Windows.Forms.DockStyle.Left;
            this.chkDivByCount.Location = new System.Drawing.Point(99, 3);
            this.chkDivByCount.Name = "chkDivByCount";
            this.chkDivByCount.Size = new System.Drawing.Size(72, 17);
            this.chkDivByCount.TabIndex = 37;
            this.chkDivByCount.Text = "除以口數";
            this.chkDivByCount.UseVisualStyleBackColor = true;
            this.chkDivByCount.CheckedChanged += new System.EventHandler(this.chkDivByCount_CheckedChanged);
            // 
            // btnAdd
            // 
            this.btnAdd.BackgroundImage = ((System.Drawing.Image)(resources.GetObject("btnAdd.BackgroundImage")));
            this.btnAdd.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Center;
            this.btnAdd.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnAdd.Location = new System.Drawing.Point(0, 0);
            this.btnAdd.Margin = new System.Windows.Forms.Padding(0, 0, 1, 0);
            this.btnAdd.Name = "btnAdd";
            this.btnAdd.Size = new System.Drawing.Size(23, 23);
            this.btnAdd.TabIndex = 38;
            this.btnAdd.UseVisualStyleBackColor = true;
            this.btnAdd.Click += new System.EventHandler(this.btnAdd_Click);
            // 
            // tableLayoutPanel3
            // 
            this.tableLayoutPanel3.AutoSize = true;
            this.tableLayoutPanel3.AutoSizeMode = System.Windows.Forms.AutoSizeMode.GrowAndShrink;
            this.tableLayoutPanel3.ColumnCount = 6;
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.Controls.Add(this.chkRangeAll, 1, 0);
            this.tableLayoutPanel3.Controls.Add(this.label1, 2, 0);
            this.tableLayoutPanel3.Controls.Add(this.dtRangeStart, 3, 0);
            this.tableLayoutPanel3.Controls.Add(this.dtRangeEnd, 5, 0);
            this.tableLayoutPanel3.Controls.Add(this.label2, 4, 0);
            this.tableLayoutPanel3.Controls.Add(this.label3, 0, 0);
            this.tableLayoutPanel3.Dock = System.Windows.Forms.DockStyle.Left;
            this.tableLayoutPanel3.Location = new System.Drawing.Point(0, 0);
            this.tableLayoutPanel3.Margin = new System.Windows.Forms.Padding(0);
            this.tableLayoutPanel3.Name = "tableLayoutPanel3";
            this.tableLayoutPanel3.RowCount = 1;
            this.tableLayoutPanel3.RowStyles.Add(new System.Windows.Forms.RowStyle());
            this.tableLayoutPanel3.Size = new System.Drawing.Size(321, 25);
            this.tableLayoutPanel3.TabIndex = 52;
            // 
            // chkRangeAll
            // 
            this.chkRangeAll.AutoSize = true;
            this.chkRangeAll.Checked = true;
            this.chkRangeAll.CheckState = System.Windows.Forms.CheckState.Checked;
            this.chkRangeAll.Dock = System.Windows.Forms.DockStyle.Left;
            this.chkRangeAll.Location = new System.Drawing.Point(73, 3);
            this.chkRangeAll.Margin = new System.Windows.Forms.Padding(0, 3, 0, 0);
            this.chkRangeAll.Name = "chkRangeAll";
            this.chkRangeAll.Size = new System.Drawing.Size(48, 22);
            this.chkRangeAll.TabIndex = 1;
            this.chkRangeAll.Text = "全部";
            this.chkRangeAll.UseVisualStyleBackColor = true;
            this.chkRangeAll.CheckedChanged += new System.EventHandler(this.chkRangeAll_CheckedChanged);
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Dock = System.Windows.Forms.DockStyle.Left;
            this.label1.Location = new System.Drawing.Point(121, 0);
            this.label1.Margin = new System.Windows.Forms.Padding(0);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(15, 25);
            this.label1.TabIndex = 2;
            this.label1.Text = "or";
            this.label1.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // dtRangeStart
            // 
            this.dtRangeStart.CustomFormat = "yyyy/MM/dd";
            this.dtRangeStart.Enabled = false;
            this.dtRangeStart.Format = System.Windows.Forms.DateTimePickerFormat.Custom;
            this.dtRangeStart.Location = new System.Drawing.Point(139, 3);
            this.dtRangeStart.Margin = new System.Windows.Forms.Padding(3, 3, 0, 0);
            this.dtRangeStart.Name = "dtRangeStart";
            this.dtRangeStart.Size = new System.Drawing.Size(84, 22);
            this.dtRangeStart.TabIndex = 3;
            this.dtRangeStart.ValueChanged += new System.EventHandler(this.dtRange_ValueChanged);
            // 
            // dtRangeEnd
            // 
            this.dtRangeEnd.CustomFormat = "yyyy/MM/dd";
            this.dtRangeEnd.Enabled = false;
            this.dtRangeEnd.Format = System.Windows.Forms.DateTimePickerFormat.Custom;
            this.dtRangeEnd.Location = new System.Drawing.Point(237, 3);
            this.dtRangeEnd.Margin = new System.Windows.Forms.Padding(0, 3, 0, 0);
            this.dtRangeEnd.Name = "dtRangeEnd";
            this.dtRangeEnd.Size = new System.Drawing.Size(84, 22);
            this.dtRangeEnd.TabIndex = 4;
            this.dtRangeEnd.ValueChanged += new System.EventHandler(this.dtRange_ValueChanged);
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Dock = System.Windows.Forms.DockStyle.Left;
            this.label2.Location = new System.Drawing.Point(223, 0);
            this.label2.Margin = new System.Windows.Forms.Padding(0, 0, 3, 0);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(11, 25);
            this.label2.TabIndex = 5;
            this.label2.Text = "~";
            this.label2.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Dock = System.Windows.Forms.DockStyle.Left;
            this.label3.Location = new System.Drawing.Point(3, 3);
            this.label3.Margin = new System.Windows.Forms.Padding(3, 3, 5, 0);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(65, 22);
            this.label3.TabIndex = 6;
            this.label3.Text = "資料範圍：";
            this.label3.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // FormEquityManage
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 12F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(371, 321);
            this.CloseButton = false;
            this.CloseButtonVisible = false;
            this.Controls.Add(this.tableLayoutPanel1);
            this.Font = new System.Drawing.Font("PMingLiU", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(136)));
            this.Name = "FormEquityManage";
            this.Text = "策略組合管理";
            this.tableLayoutPanel1.ResumeLayout(false);
            this.tableLayoutPanel1.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dvEquityList)).EndInit();
            this.tableLayoutPanel2.ResumeLayout(false);
            this.tableLayoutPanel2.PerformLayout();
            this.tableLayoutPanel3.ResumeLayout(false);
            this.tableLayoutPanel3.PerformLayout();
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.TableLayoutPanel tableLayoutPanel1;
        private System.Windows.Forms.DataGridView dvEquityList;
        private System.Windows.Forms.CheckBox chkDivByCount;
        private System.Windows.Forms.TableLayoutPanel tableLayoutPanel2;
        private System.Windows.Forms.Button btnMoveDown;
        private System.Windows.Forms.Button btnMoveUp;
        private System.Windows.Forms.Button btnAdd;
        private System.Windows.Forms.TableLayoutPanel tableLayoutPanel3;
        private System.Windows.Forms.CheckBox chkRangeAll;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.DateTimePicker dtRangeStart;
        private System.Windows.Forms.DateTimePicker dtRangeEnd;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.Button btnFixProfit;
    }
}