namespace VisualPortfolio.Forms
{
    partial class FormCommission
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
            this.menuMain = new System.Windows.Forms.MenuStrip();
            this.mtnConfig = new System.Windows.Forms.ToolStripMenuItem();
            this.reportCommission = new Microsoft.Reporting.WinForms.ReportViewer();
            this.menuMain.SuspendLayout();
            this.SuspendLayout();
            // 
            // menuMain
            // 
            this.menuMain.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.mtnConfig});
            this.menuMain.Location = new System.Drawing.Point(0, 0);
            this.menuMain.Name = "menuMain";
            this.menuMain.Size = new System.Drawing.Size(284, 24);
            this.menuMain.TabIndex = 3;
            this.menuMain.Text = "menuMain";
            // 
            // mtnConfig
            // 
            this.mtnConfig.Name = "mtnConfig";
            this.mtnConfig.Size = new System.Drawing.Size(57, 20);
            this.mtnConfig.Text = "Config";
            this.mtnConfig.Click += new System.EventHandler(this.mtnConfig_Click);
            // 
            // reportCommission
            // 
            this.reportCommission.Dock = System.Windows.Forms.DockStyle.Fill;
            this.reportCommission.LocalReport.ReportEmbeddedResource = "VisualPortfolio.ReportCommission.rdlc";
            this.reportCommission.Location = new System.Drawing.Point(0, 24);
            this.reportCommission.Name = "reportCommission";
            this.reportCommission.Size = new System.Drawing.Size(284, 238);
            this.reportCommission.TabIndex = 4;
            this.reportCommission.ZoomMode = Microsoft.Reporting.WinForms.ZoomMode.PageWidth;
            // 
            // FormCommission
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 12F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(284, 262);
            this.CloseButton = false;
            this.CloseButtonVisible = false;
            this.Controls.Add(this.reportCommission);
            this.Controls.Add(this.menuMain);
            this.Font = new System.Drawing.Font("PMingLiU", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(136)));
            this.MainMenuStrip = this.menuMain;
            this.Name = "FormCommission";
            this.Text = "分潤退傭";
            this.menuMain.ResumeLayout(false);
            this.menuMain.PerformLayout();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion
        private System.Windows.Forms.MenuStrip menuMain;
        private System.Windows.Forms.ToolStripMenuItem mtnConfig;
        private Microsoft.Reporting.WinForms.ReportViewer reportCommission;
    }
}