using System;
using System.Reflection;
using System.Windows.Forms;
using SharpUpdate;
using System.Drawing;

namespace VisualPortfolio
{
    public partial class FormAbout : Form, ISharpUpdatable
    {
        public FormAbout()
        {
            InitializeComponent();
        }

        private void frmAbout_Load(object sender, EventArgs e)
        {
            lbVersion.Text = "VisualPortfolio " + this.ApplicationVersion;
        }

        private void btnUpdate_Click(object sender, EventArgs e)
        {
            var updater = new SharpUpdater(this);
            updater.DoUpdate();
        }

        #region Auto-Update
        public string ApplicationName
        {
            get { return "VisualPortfolio"; }
        }

        public string ApplicationID
        {
            get { return "VisualPortfolio"; }
        }

        public string ApplicationCode
        {
            get { return "V2019A"; }
        }

        public string ApplicationVersion
        {
            get
            {
                Version ver = Assembly.GetExecutingAssembly().GetName().Version;
                DateTime buildDateTime = new DateTime(2000, 1, 1).Add(new TimeSpan(TimeSpan.TicksPerDay * ver.Build)); // days since 1 January 2000
                return string.Format("v{0:yy.MM.dd}.{1:00000}", buildDateTime, ver.Revision);
            }
        }

        public Assembly ApplicationAssembly
        {
            get { return Assembly.GetExecutingAssembly(); }
        }

        public Icon ApplicationIcon
        {
            get { return this.Icon; }
        }

        public Uri UpdateXmlLocation
        {
            get { return new Uri("https://bitbucket.org/sibuzu/superjackupdate/raw/master/update.xml"); }
        }

        public Form Context
        {
            get { return this; }
        }

        #endregion
    }
}
