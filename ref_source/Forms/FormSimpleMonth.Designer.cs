namespace VisualPortfolio.Forms
{
    partial class FormSimpleMonth
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
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(FormSimpleMonth));
            this.tableLayoutPanel3 = new System.Windows.Forms.TableLayoutPanel();
            this.label3 = new System.Windows.Forms.Label();
            this.cbInterval = new System.Windows.Forms.ComboBox();
            this.label1 = new System.Windows.Forms.Label();
            this.cbKind = new System.Windows.Forms.ComboBox();
            this.label2 = new System.Windows.Forms.Label();
            this.surfProfitMonth = new NPlot.Windows.PlotSurface2D();
            this.btnSave = new System.Windows.Forms.Button();
            this.btnCopy = new System.Windows.Forms.Button();
            this.spinRolling = new System.Windows.Forms.NumericUpDown();
            this.tableLayoutPanel3.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.spinRolling)).BeginInit();
            this.SuspendLayout();
            // 
            // tableLayoutPanel3
            // 
            this.tableLayoutPanel3.ColumnCount = 8;
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel3.Controls.Add(this.label3, 4, 0);
            this.tableLayoutPanel3.Controls.Add(this.cbInterval, 3, 0);
            this.tableLayoutPanel3.Controls.Add(this.label1, 2, 0);
            this.tableLayoutPanel3.Controls.Add(this.cbKind, 1, 0);
            this.tableLayoutPanel3.Controls.Add(this.label2, 0, 0);
            this.tableLayoutPanel3.Controls.Add(this.surfProfitMonth, 0, 1);
            this.tableLayoutPanel3.Controls.Add(this.btnSave, 7, 0);
            this.tableLayoutPanel3.Controls.Add(this.btnCopy, 6, 0);
            this.tableLayoutPanel3.Controls.Add(this.spinRolling, 5, 0);
            this.tableLayoutPanel3.Dock = System.Windows.Forms.DockStyle.Fill;
            this.tableLayoutPanel3.Location = new System.Drawing.Point(0, 0);
            this.tableLayoutPanel3.Name = "tableLayoutPanel3";
            this.tableLayoutPanel3.RowCount = 2;
            this.tableLayoutPanel3.RowStyles.Add(new System.Windows.Forms.RowStyle());
            this.tableLayoutPanel3.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableLayoutPanel3.Size = new System.Drawing.Size(556, 192);
            this.tableLayoutPanel3.TabIndex = 3;
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Dock = System.Windows.Forms.DockStyle.Left;
            this.label3.Font = new System.Drawing.Font("PMingLiU", 11.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(136)));
            this.label3.Location = new System.Drawing.Point(361, 0);
            this.label3.Margin = new System.Windows.Forms.Padding(3, 0, 0, 0);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(82, 29);
            this.label3.TabIndex = 13;
            this.label3.Text = "滾動因子：";
            this.label3.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // cbInterval
            // 
            this.cbInterval.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cbInterval.FormattingEnabled = true;
            this.cbInterval.Items.AddRange(new object[] {
            "全部"});
            this.cbInterval.Location = new System.Drawing.Point(243, 3);
            this.cbInterval.Name = "cbInterval";
            this.cbInterval.Size = new System.Drawing.Size(112, 20);
            this.cbInterval.TabIndex = 12;
            this.cbInterval.SelectedIndexChanged += new System.EventHandler(this.cbKind_SelectedIndexChanged);
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Dock = System.Windows.Forms.DockStyle.Left;
            this.label1.Font = new System.Drawing.Font("PMingLiU", 11.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(136)));
            this.label1.Location = new System.Drawing.Point(188, 0);
            this.label1.Margin = new System.Windows.Forms.Padding(3, 0, 0, 0);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(52, 29);
            this.label1.TabIndex = 11;
            this.label1.Text = "範圍：";
            this.label1.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // cbKind
            // 
            this.cbKind.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cbKind.FormattingEnabled = true;
            this.cbKind.Items.AddRange(new object[] {
            "獲利",
            "Drawdown",
            "獲利+Drawdown",
            "獲利(個別)",
            "Drawdown(個別)"});
            this.cbKind.Location = new System.Drawing.Point(58, 3);
            this.cbKind.Name = "cbKind";
            this.cbKind.Size = new System.Drawing.Size(124, 20);
            this.cbKind.TabIndex = 4;
            this.cbKind.SelectedIndexChanged += new System.EventHandler(this.cbKind_SelectedIndexChanged);
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Dock = System.Windows.Forms.DockStyle.Left;
            this.label2.Font = new System.Drawing.Font("PMingLiU", 11.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(136)));
            this.label2.Location = new System.Drawing.Point(3, 0);
            this.label2.Margin = new System.Windows.Forms.Padding(3, 0, 0, 0);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(52, 29);
            this.label2.TabIndex = 3;
            this.label2.Text = "類別：";
            this.label2.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // surfProfitMonth
            // 
            this.surfProfitMonth.AutoScaleAutoGeneratedAxes = false;
            this.surfProfitMonth.AutoScaleTitle = false;
            this.surfProfitMonth.BackColor = System.Drawing.SystemColors.ControlLightLight;
            this.tableLayoutPanel3.SetColumnSpan(this.surfProfitMonth, 8);
            this.surfProfitMonth.DateTimeToolTip = false;
            this.surfProfitMonth.Dock = System.Windows.Forms.DockStyle.Fill;
            this.surfProfitMonth.Legend = null;
            this.surfProfitMonth.LegendZOrder = -1;
            this.surfProfitMonth.Location = new System.Drawing.Point(3, 32);
            this.surfProfitMonth.Name = "surfProfitMonth";
            this.surfProfitMonth.RightMenu = null;
            this.surfProfitMonth.ShowCoordinates = false;
            this.surfProfitMonth.Size = new System.Drawing.Size(552, 157);
            this.surfProfitMonth.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.None;
            this.surfProfitMonth.TabIndex = 1;
            this.surfProfitMonth.Text = "plotSurface2D1";
            this.surfProfitMonth.Title = "";
            this.surfProfitMonth.TitleFont = new System.Drawing.Font("Arial", 14F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Pixel);
            this.surfProfitMonth.XAxis1 = null;
            this.surfProfitMonth.XAxis2 = null;
            this.surfProfitMonth.YAxis1 = null;
            this.surfProfitMonth.YAxis2 = null;
            // 
            // btnSave
            // 
            this.btnSave.BackgroundImage = ((System.Drawing.Image)(resources.GetObject("btnSave.BackgroundImage")));
            this.btnSave.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Center;
            this.btnSave.FlatStyle = System.Windows.Forms.FlatStyle.Popup;
            this.btnSave.Location = new System.Drawing.Point(532, 3);
            this.btnSave.Name = "btnSave";
            this.btnSave.Size = new System.Drawing.Size(23, 23);
            this.btnSave.TabIndex = 10;
            this.btnSave.UseVisualStyleBackColor = true;
            this.btnSave.Click += new System.EventHandler(this.btnSave_Click);
            // 
            // btnCopy
            // 
            this.btnCopy.BackgroundImage = ((System.Drawing.Image)(resources.GetObject("btnCopy.BackgroundImage")));
            this.btnCopy.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Center;
            this.btnCopy.FlatStyle = System.Windows.Forms.FlatStyle.Popup;
            this.btnCopy.Location = new System.Drawing.Point(503, 3);
            this.btnCopy.Name = "btnCopy";
            this.btnCopy.Size = new System.Drawing.Size(23, 23);
            this.btnCopy.TabIndex = 9;
            this.btnCopy.UseVisualStyleBackColor = true;
            this.btnCopy.Click += new System.EventHandler(this.btnCopy_Click);
            // 
            // spinRolling
            // 
            this.spinRolling.Location = new System.Drawing.Point(446, 3);
            this.spinRolling.Maximum = new decimal(new int[] {
            999999,
            0,
            0,
            0});
            this.spinRolling.Minimum = new decimal(new int[] {
            1,
            0,
            0,
            0});
            this.spinRolling.Name = "spinRolling";
            this.spinRolling.Size = new System.Drawing.Size(51, 22);
            this.spinRolling.TabIndex = 14;
            this.spinRolling.Value = new decimal(new int[] {
            1,
            0,
            0,
            0});
            this.spinRolling.ValueChanged += new System.EventHandler(this.cbKind_SelectedIndexChanged);
            // 
            // FormSimpleMonth
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 12F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(556, 192);
            this.CloseButton = false;
            this.CloseButtonVisible = false;
            this.Controls.Add(this.tableLayoutPanel3);
            this.Font = new System.Drawing.Font("PMingLiU", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(136)));
            this.Name = "FormSimpleMonth";
            this.Text = "逐年獲利";
            this.tableLayoutPanel3.ResumeLayout(false);
            this.tableLayoutPanel3.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.spinRolling)).EndInit();
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.TableLayoutPanel tableLayoutPanel3;
        private System.Windows.Forms.ComboBox cbKind;
        private System.Windows.Forms.Label label2;
        private NPlot.Windows.PlotSurface2D surfProfitMonth;
        private System.Windows.Forms.Button btnSave;
        private System.Windows.Forms.Button btnCopy;
        private System.Windows.Forms.ComboBox cbInterval;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.NumericUpDown spinRolling;
    }
}