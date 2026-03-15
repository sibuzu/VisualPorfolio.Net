namespace VisualPortfolio
{
    partial class FormOptions
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
            this.btnOK = new System.Windows.Forms.Button();
            this.btnCancel = new System.Windows.Forms.Button();
            this.label6 = new System.Windows.Forms.Label();
            this.tbMddCount = new System.Windows.Forms.TextBox();
            this.chk計算每日DD = new System.Windows.Forms.CheckBox();
            this.groupBox1 = new System.Windows.Forms.GroupBox();
            this.tbCapital = new System.Windows.Forms.TextBox();
            this.label1 = new System.Windows.Forms.Label();
            this.tbRiskFreeRate = new System.Windows.Forms.TextBox();
            this.label2 = new System.Windows.Forms.Label();
            this.groupBox1.SuspendLayout();
            this.SuspendLayout();
            // 
            // btnOK
            // 
            this.btnOK.DialogResult = System.Windows.Forms.DialogResult.OK;
            this.btnOK.Location = new System.Drawing.Point(24, 135);
            this.btnOK.Name = "btnOK";
            this.btnOK.Size = new System.Drawing.Size(75, 21);
            this.btnOK.TabIndex = 5;
            this.btnOK.Text = "OK";
            this.btnOK.UseVisualStyleBackColor = true;
            // 
            // btnCancel
            // 
            this.btnCancel.DialogResult = System.Windows.Forms.DialogResult.Cancel;
            this.btnCancel.Location = new System.Drawing.Point(105, 135);
            this.btnCancel.Name = "btnCancel";
            this.btnCancel.Size = new System.Drawing.Size(75, 21);
            this.btnCancel.TabIndex = 6;
            this.btnCancel.Text = "Cancel";
            this.btnCancel.UseVisualStyleBackColor = true;
            // 
            // label6
            // 
            this.label6.AutoSize = true;
            this.label6.Location = new System.Drawing.Point(15, 9);
            this.label6.Name = "label6";
            this.label6.Size = new System.Drawing.Size(58, 12);
            this.label6.TabIndex = 16;
            this.label6.Text = "MDD數目:";
            // 
            // tbMddCount
            // 
            this.tbMddCount.Location = new System.Drawing.Point(80, 7);
            this.tbMddCount.Name = "tbMddCount";
            this.tbMddCount.Size = new System.Drawing.Size(100, 22);
            this.tbMddCount.TabIndex = 17;
            this.tbMddCount.Text = "5";
            // 
            // chk計算每日DD
            // 
            this.chk計算每日DD.AutoSize = true;
            this.chk計算每日DD.Location = new System.Drawing.Point(17, 35);
            this.chk計算每日DD.Name = "chk計算每日DD";
            this.chk計算每日DD.Size = new System.Drawing.Size(88, 16);
            this.chk計算每日DD.TabIndex = 18;
            this.chk計算每日DD.Text = "計算每日DD";
            this.chk計算每日DD.UseVisualStyleBackColor = true;
            // 
            // groupBox1
            // 
            this.groupBox1.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.groupBox1.Controls.Add(this.tbRiskFreeRate);
            this.groupBox1.Controls.Add(this.label2);
            this.groupBox1.Controls.Add(this.tbCapital);
            this.groupBox1.Controls.Add(this.label1);
            this.groupBox1.Location = new System.Drawing.Point(17, 58);
            this.groupBox1.Name = "groupBox1";
            this.groupBox1.Size = new System.Drawing.Size(165, 71);
            this.groupBox1.TabIndex = 19;
            this.groupBox1.TabStop = false;
            this.groupBox1.Text = " Sharpe Ratio ";
            // 
            // tbCapital
            // 
            this.tbCapital.Location = new System.Drawing.Point(88, 16);
            this.tbCapital.Name = "tbCapital";
            this.tbCapital.Size = new System.Drawing.Size(66, 22);
            this.tbCapital.TabIndex = 19;
            this.tbCapital.Text = "100";
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(6, 20);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(52, 12);
            this.label1.TabIndex = 18;
            this.label1.Text = "本金(萬):";
            // 
            // tbRiskFreeRate
            // 
            this.tbRiskFreeRate.Location = new System.Drawing.Point(88, 41);
            this.tbRiskFreeRate.Name = "tbRiskFreeRate";
            this.tbRiskFreeRate.Size = new System.Drawing.Size(66, 22);
            this.tbRiskFreeRate.TabIndex = 21;
            this.tbRiskFreeRate.Text = "3";
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(6, 45);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(85, 12);
            this.label2.TabIndex = 20;
            this.label2.Text = "無風險利率(%):";
            // 
            // FormOptions
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 12F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(194, 168);
            this.Controls.Add(this.groupBox1);
            this.Controls.Add(this.chk計算每日DD);
            this.Controls.Add(this.tbMddCount);
            this.Controls.Add(this.label6);
            this.Controls.Add(this.btnCancel);
            this.Controls.Add(this.btnOK);
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "FormOptions";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterParent;
            this.Text = "Options";
            this.groupBox1.ResumeLayout(false);
            this.groupBox1.PerformLayout();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion
        private System.Windows.Forms.Button btnOK;
        private System.Windows.Forms.Button btnCancel;
        private System.Windows.Forms.Label label6;
        private System.Windows.Forms.TextBox tbMddCount;
        private System.Windows.Forms.CheckBox chk計算每日DD;
        private System.Windows.Forms.GroupBox groupBox1;
        private System.Windows.Forms.TextBox tbRiskFreeRate;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.TextBox tbCapital;
        private System.Windows.Forms.Label label1;
    }
}