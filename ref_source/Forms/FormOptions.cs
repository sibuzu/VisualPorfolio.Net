using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;

namespace VisualPortfolio
{
    public partial class FormOptions : Form
    {
        public FormOptions()
        {
            InitializeComponent();
        }

        public int mddCount
        {
            get { return Convert.ToInt32(this.tbMddCount.Text); }
            set { this.tbMddCount.Text = value.ToString(); }
        }

        public double capital
        {
            get { return Convert.ToDouble(this.tbCapital.Text); }
            set { this.tbCapital.Text = value.ToString(); }
        }

        public double riskFreeRate
        {
            get { return Convert.ToDouble(this.tbRiskFreeRate.Text); }
            set { this.tbRiskFreeRate.Text = value.ToString(); }
        }

        public bool 計算每日DD
        {
            get { return chk計算每日DD.Checked; }
            set { chk計算每日DD.Checked = value; }
        }
    }
}
