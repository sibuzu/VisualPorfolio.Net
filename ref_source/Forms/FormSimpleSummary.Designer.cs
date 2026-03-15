namespace VisualPortfolio.Forms
{
    partial class FormSimpleSummary
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
            this.reportSummary = new Microsoft.Reporting.WinForms.ReportViewer();
            this.SuspendLayout();
            // 
            // reportSummary
            // 
            this.reportSummary.Dock = System.Windows.Forms.DockStyle.Fill;
            this.reportSummary.LocalReport.ReportEmbeddedResource = "VisualPortfolio.ReportSummary.rdlc";
            this.reportSummary.Location = new System.Drawing.Point(0, 0);
            this.reportSummary.Name = "reportSummary";
            this.reportSummary.Size = new System.Drawing.Size(284, 262);
            this.reportSummary.TabIndex = 1;
            this.reportSummary.ZoomMode = Microsoft.Reporting.WinForms.ZoomMode.PageWidth;
            // 
            // FormSimpleSummary
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 12F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(284, 262);
            this.CloseButton = false;
            this.CloseButtonVisible = false;
            this.Controls.Add(this.reportSummary);
            this.Font = new System.Drawing.Font("PMingLiU", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(136)));
            this.Name = "FormSimpleSummary";
            this.Text = "獲利報表";
            this.ResumeLayout(false);

        }

        #endregion

        private Microsoft.Reporting.WinForms.ReportViewer reportSummary;
    }
}