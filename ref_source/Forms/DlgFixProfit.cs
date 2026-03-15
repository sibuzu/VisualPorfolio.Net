using System;
using System.Windows.Forms;

namespace VisualPortfolio.Forms
{
    public partial class DlgFixProfit : Form
    {
        public DateTime start
        {
            get { return dtStart.Value; }
            set { dtStart.Value = value; }
        }

        public DateTime end
        {
            get { return dtEnd.Value; }
            set { dtEnd.Value = value; }
        }

        public decimal profit
        {
            get
            {
                try
                {
                    return decimal.Parse(tbProfit.Text);
                }
                catch
                {
                    return 10000;
                }
            }
            set { tbProfit.Text = value.ToString(); }
        }

        public DlgFixProfit()
        {
            InitializeComponent();
            profit = 10000;
        }
    }
}
