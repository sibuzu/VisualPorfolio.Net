using System;
using System.Windows.Forms;

namespace VisualPortfolio
{
    public partial class DlgPropertyGrid : Form, IUpdateUIVisibily
    {
        #region init
        public DlgPropertyGrid()
        {
            InitializeComponent();
        }
        #endregion

        #region methods
        public void SetReadOnly(bool readOnly)
        {
            pgMain.Enabled = !readOnly;
        }

        public void SetSelectedObject(object obj)
        {
            pgMain.SelectedObject = obj;
        }
        #endregion

        #region UI Visibility
        public void UpdatePropertyGrid()
        {
            pgMain.Refresh();
        }
        #endregion
    }
}
