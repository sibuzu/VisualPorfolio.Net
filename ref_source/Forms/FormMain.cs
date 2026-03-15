using VisualPortfolio.Forms;
using System;
using System.Collections.Generic;
using System.Data;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using System.Windows.Forms;
using System.Xml;
using WeifenLuo.WinFormsUI.Docking;
using System.Drawing;
using VisualPortfolio.Classes;
using System.ComponentModel;
using System.Linq;

namespace VisualPortfolio
{
    public partial class FormMain : Form
    {
        private DeserializeDockContent m_deserializeDockContent;

        static void MyHandler(object sender, UnhandledExceptionEventArgs args)
        {
            Exception e = (Exception)args.ExceptionObject;
            MessageBox.Show(e.Message);
        }

        public FormMain()
        {
            AppDomain currentDomain = AppDomain.CurrentDomain;
            currentDomain.UnhandledException += new UnhandledExceptionEventHandler(MyHandler);

            Global.RawPortfolioList = new List<ClsTradeItem>();
            Global.PortfolioList = new List<ClsTradeItem>();
            Global.listEquityAttr = new ClsListEquity();
            Global.listResult = new ClsExecResultList();
            Global.listBatchRun = new ClsBatchRunList();
            Global.listWinLoss = new ClsWinLossList();

            InitializeComponent();
            Global.frmMain = this;
            Global.frmSimpleSummary = new FormSimpleSummary();
            Global.frmSimplePlot = new FormSimplePlot();
            Global.frmSimpleMonth = new FormSimpleMonth();
            Global.frmEquityManage = new FormEquityManage();
            Global.frmPositionAnalysis = new FormPositionAnalysis();
            Global.frmResultSummary = new FormResultSummary();
            Global.frmWinLoss = new FormWinLoss();
            Global.frmCommission = new FormCommission();
            Global.frmDiversity = new FormDiversity();
            m_deserializeDockContent = new DeserializeDockContent(GetContentFromPersistString);

            try
            {
                LoadXmlConfig();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Exception: {ex}");
            }
            Global.SummaryReport = new TSummaryReport();
        }

        #region XmlUtil
        public static string XmlGetString(XmlNode xn, string name, string defval = "")
        {
            try { return xn.SelectSingleNode(name).InnerText; }
            catch { return defval; }
        }
        public static decimal XmlGetDecimal(XmlNode xn, string name, decimal defval = 0)
        {
            try { return Convert.ToDecimal(xn.SelectSingleNode(name).InnerText); }
            catch { return defval; }
        }
        public static double XmlGetDouble(XmlNode xn, string name, double defval = 0)
        {
            try { return Convert.ToDouble(xn.SelectSingleNode(name).InnerText); }
            catch { return defval; }
        }
        public static int XmlGetInt32(XmlNode xn, string name, int defval = 0)
        {
            try { return Convert.ToInt32(xn.SelectSingleNode(name).InnerText); }
            catch { return defval; }
        }
        #endregion

        private void tbOpen_Click(object sender, EventArgs e)
        {
            // Create an instance of the open file dialog box.
            OpenFileDialog dlgOpen = new OpenFileDialog();

            // Set filter options and filter index.
            dlgOpen.Filter = "Portfolio File|*.pfo|All Files|*.*";
            dlgOpen.FilterIndex = 1;
            dlgOpen.Multiselect = false;

            // Call the ShowDialog method to show the dialog box.
            DialogResult userClickedOK = dlgOpen.ShowDialog();

            // Process input if the user clicked OK.
            if (userClickedOK == DialogResult.OK)
            {
                try
                {
                    Application.UseWaitCursor = true;
                    LoadProject(dlgOpen.FileName);
                }
                finally
                {
                    Application.UseWaitCursor = false;
                }
            }

            // UpdateButtonColor();
        }

        private void tbSave_Click(object sender, EventArgs e)
        {
            // Create an instance of the open file dialog box.
            SaveFileDialog dlgOpen = new SaveFileDialog();

            // Set filter options and filter index.
            dlgOpen.Filter = "Portfolio File|*.pfo|All Files|*.*";
            dlgOpen.FilterIndex = 1;

            // Call the ShowDialog method to show the dialog box.
            DialogResult userClickedOK = dlgOpen.ShowDialog();

            // Process input if the user clicked OK.
            if (userClickedOK == DialogResult.OK)
            {
                SaveProject(dlgOpen.FileName);
            }
        }

        private void tbExport_Click(object sender, EventArgs e)
        {
            // Create an instance of the open file dialog box.
            SaveFileDialog dlgOpen = new SaveFileDialog();

            // Set filter options and filter index.
            dlgOpen.Filter = "Export File|*.xml;*.srp;*.xrp|All Files|*.*";
            dlgOpen.FilterIndex = 1;

            // Call the ShowDialog method to show the dialog box.
            DialogResult userClickedOK = dlgOpen.ShowDialog();

            // Process input if the user clicked OK.
            if (userClickedOK == DialogResult.OK)
            {
                TSummaryReport.ExportMergeTrade(dlgOpen.FileName, Global.PortfolioList);
            }
        }

        private void frmMain_Load(object sender, EventArgs e)
        {
            string[] args = Environment.GetCommandLineArgs();

            if (args.Length == 2)
            {
                try
                {
                    LoadProject(args[1]);
                }
                catch (Exception ex)
                {
                    MessageBox.Show(ex.Message);
                }
            }

            Version ver = typeof(FormMain).Assembly.GetName().Version;
            DateTime buildDateTime = new DateTime(2000, 1, 1).Add(new TimeSpan(TimeSpan.TicksPerDay * ver.Build)); // days since 1 January 2000
            this.Text = string.Format("[Visual Portfolio v{0}.{1}]", buildDateTime.ToString("yy.MM.dd"), ver.Revision);

            string configFile = Global.DockPanelFile;

            if (File.Exists(configFile))
            {
                dockPanel.LoadFromXml(configFile, m_deserializeDockContent);
            }
            else
            {
                Assembly assembly = GetType().Module.Assembly;
                Stream xmlStream = assembly.GetManifestResourceStream("VisualPortfolio.Resources.ReportPanel.xml");
                dockPanel.LoadFromXml(xmlStream, m_deserializeDockContent);
                xmlStream.Close();
            }

            Global.frmSimplePlot.Show(dockPanel);
            Global.frmSimpleMonth.Show(dockPanel);
            Global.frmEquityManage.Show(dockPanel);
            Global.frmPositionAnalysis.Show(dockPanel);
            Global.frmResultSummary.Show(dockPanel);
            Global.frmWinLoss.Show(dockPanel);
            Global.frmSimpleSummary.Show(dockPanel);
            Global.frmCommission.Show(dockPanel);
            Global.frmDiversity.Show(dockPanel);
            Global.frmEquityManage.UpdateButtonColor();
        }

        private IDockContent GetContentFromPersistString(string persistString)
        {
            if (persistString == typeof(FormSimpleSummary).ToString())
                return Global.frmSimpleSummary;
            else if (persistString == typeof(FormSimplePlot).ToString())
                return Global.frmSimplePlot;
            else if (persistString == typeof(FormSimpleMonth).ToString())
                return Global.frmSimpleMonth;
            else if (persistString == typeof(FormEquityManage).ToString())
                return Global.frmEquityManage;
            else if (persistString == typeof(FormPositionAnalysis).ToString())
                return Global.frmPositionAnalysis;
            else if (persistString == typeof(FormResultSummary).ToString())
                return Global.frmResultSummary;
            else if (persistString == typeof(FormWinLoss).ToString())
                return Global.frmWinLoss;
            else if (persistString == typeof(FormCommission).ToString())
                return Global.frmCommission;
            else if (persistString == typeof(FormDiversity).ToString())
                return Global.frmDiversity;
            else
                return null;
        }

        private void LoadProject(string fileName)
        {
            XmlDocument x = new XmlDocument();
            try
            {
                ClearProject();

                if (!File.Exists(fileName)) return;
                x.Load(fileName);
                string projPath = Path.GetDirectoryName(fileName);

                // t2 = watch.Elapsed.TotalSeconds;
                // sw.WriteLine("AdjustEquityCount: {0:0.000}, {1:0.000}", t2 - t1, t2);
                // t1 = t2;

                int i = 0;
                Global.listEquityAttr.Clear();
                foreach (XmlElement elm in x.DocumentElement.ChildNodes)
                {
                    LoadFromXml(i, elm, projPath);
                    // t2 = watch.Elapsed.TotalSeconds;
                    // sw.WriteLine("LoadFromXml{2}: {0:0.000}, {1:0.000}", t2 - t1, t2, i);
                    // t1 = t2;
                    i++;
                }

                Global.listEquityAttr.ResetIndex();
                UpdateButtonColor();
                UpdatePortfolio();
                UpdateDraw();
            }
            catch (Exception e)
            {
                MessageBox.Show(e.Message);
            }
        }

        private void SaveProject(string fileName)
        {
            XmlTextWriter xmlOut = new XmlTextWriter(fileName, Encoding.UTF8);

            // Use indenting for readability
            xmlOut.Formatting = Formatting.Indented;
            xmlOut.WriteStartDocument();

            // Write comments
            xmlOut.WriteComment("Portfolio Trade List");

            // Write first element
            xmlOut.WriteStartElement("PortfolioyList");

            foreach (var ea in Global.listEquityAttr)
            {
                xmlOut.WriteStartElement("Equity");
                xmlOut.WriteAttributeString("Index", ea.Index.ToString());
                xmlOut.WriteAttributeString("FileName", ea.FileName);
                xmlOut.WriteAttributeString("Color", System.Drawing.ColorTranslator.ToHtml(ea.Color));
                xmlOut.WriteAttributeString("Count", ea.Contract.ToString());
                xmlOut.WriteAttributeString("Weight", ea.Weight.ToString());
                if (!string.IsNullOrEmpty(ea.名稱)) xmlOut.WriteAttributeString("名稱", ea.名稱.ToString());
                xmlOut.WriteEndElement();
            }

            xmlOut.WriteEndElement();

            xmlOut.WriteEndDocument();
            xmlOut.Close();
        }

        private void ClearProject()
        {
        }

        internal void LoadFromXml(int i, XmlElement elm, string projPath)
        {
            ClsEquityAttr ea = new ClsEquityAttr();

            try
            {
                var fname = elm.Attributes["FileName"].Value;
                if (!File.Exists(fname))
                {
                    fname = Path.Combine(projPath, Path.GetFileName(fname));
                }

                ea.FileName = fname;
                ea.TradeList.LoadFile(fname);
            }
            catch { }

            try
            {
                Color c = ColorTranslator.FromHtml(elm.Attributes["Color"].Value); ;
                ea.Color = c;
            }
            catch { }

            try
            {
                decimal w = decimal.Parse(elm.Attributes["Weight"].Value);
                decimal c = 1;
                if (elm.HasAttribute("Count"))
                {
                    c = decimal.Parse(elm.Attributes["Count"].Value);
                }
                if (elm.HasAttribute("名稱"))
                {
                    ea.名稱 = elm.Attributes["名稱"].Value;
                }

                if (w == 0)
                {
                    ea.Active = false;
                }
                else
                {
                    ea.Active = true;
                    ea.Contract = (int)c;
                    ea.Weight = w;
                }
            }
            catch { }

            ea.Index = i + 1;
            Global.listEquityAttr.Add(ea);
        }

        internal void UpdateButtonColor()
        {
            Global.frmEquityManage.UpdateButtonColor();
        }

        internal void UpdatePortfolio()
        {
            Global.RawPortfolioList.Clear();
            for (int i = 0; i < Global.listEquityAttr.Count; ++i)
            {
                var ea = Global.listEquityAttr[i];
                if (!ea.Active) continue;

                foreach (ClsTradeItem ti in ea.TradeList.Items)
                {
                    ti.tag = i;
                    ti.aux_count = ea.Contract;
                    ti.aux_weight = ea.Weight;
                    Global.RawPortfolioList.Add(ti);
                }
            }

            // sort by date
            Global.RawPortfolioList = Global.RawPortfolioList
                .OrderBy(o => o.tradeDate2)
                .ThenBy(o => o.idx)
                .ToList();

            Global.PortfolioList.Clear();
            Global.listWinLoss.Clear();
            if (Global.frmEquityManage != null)
            {
                var dtStart = Global.frmEquityManage.GetRangeStart().Date;
                var dtEnd = Global.frmEquityManage.GetRangeEnd().Date + new TimeSpan(23, 59, 59);
                foreach (var ti in Global.RawPortfolioList)
                {
                    if (ti.tradeDate2 < dtStart) continue;
                    if (ti.tradeDate2 > dtEnd) break;
                    Global.PortfolioList.Add(ti);
                    Global.listWinLoss.Update(ti);
                }
            }
            Global.listWinLoss.FinalUpdate();

            int idx = 0;
            foreach (ClsTradeItem ti in Global.PortfolioList)
            {
                ti.aux_idx = idx++;
            }

            Global.frmEquityManage.UpdateRangePicker();
            Global.frmSimpleSummary.CreateSimpleSummary();

            Global.frmResultSummary.UpdateResultSummary();
            Global.frmWinLoss.UpdateWinLossTable();
            Global.frmPositionAnalysis.UpdatePostionTable();
            Global.frmCommission.CreateCommissionResult();
            Global.frmDiversity.UpdateDiversityTable();
        }

        internal void UpdateDraw()
        {
            Global.frmSimplePlot.CreatePlot();
            Global.frmSimpleMonth.CreatePlot();
        }

        private void tpOptions_Click(object sender, EventArgs e)
        {
            FormOptions dlg = new FormOptions();
            dlg.mddCount = Global.MddCount;
            dlg.capital = Global.Capital;
            dlg.riskFreeRate = Global.RiskFreeRate;
            dlg.計算每日DD = Global.計算每日DD;

            if (dlg.ShowDialog() != DialogResult.OK)
                return;

            if (Global.MddCount != dlg.mddCount ||
                Global.Capital != dlg.capital || 
                Global.RiskFreeRate != dlg.riskFreeRate)
            {
                Global.MddCount = dlg.mddCount;
                Global.Capital = dlg.capital;
                Global.RiskFreeRate = dlg.riskFreeRate;
                Global.frmMain.UpdatePortfolio();
                Global.frmMain.UpdateDraw();
            }

            if (Global.計算每日DD != dlg.計算每日DD)
            {
                Global.計算每日DD = dlg.計算每日DD;
                MessageBox.Show("變動計算每日DD，需要重新啟動才有效用。");
            }
        }

        private void frmMain_FormClosed(object sender, FormClosedEventArgs e)
        {
            SaveXmlConfig();
        }

        private void frmMain_FormClosing(object sender, FormClosingEventArgs e)
        {
            dockPanel.SaveAsXml(Global.DockPanelFile);
        }

        private void SaveXmlConfig()
        {
            string xmlFile = Path.Combine(Application.StartupPath, "VisualPortfolio.xml");
            try
            {
                XmlWriterSettings settings = new XmlWriterSettings();
                settings.Indent = true;

                XmlWriter writer = XmlWriter.Create(xmlFile, settings);
                writer.WriteStartDocument();
                writer.WriteStartElement("Setting");
                writer.WriteElementString("MddCount", Global.MddCount.ToString());
                writer.WriteElementString("Capital", Global.Capital.ToString());
                writer.WriteElementString("RiskFreeRate", Global.RiskFreeRate.ToString());
                writer.WriteElementString("計算每日DD", Global.計算每日DD ? "1" : "0");
                writer.WriteElementString("Width", this.Width.ToString());
                writer.WriteElementString("Height", this.Height.ToString());

                var cfg = Global.CommissionSet.cfg;
                cfg.SaveConfig(writer);

                writer.WriteEndElement();

                writer.WriteEndDocument();

                writer.Flush();
                writer.Close();
            }
            catch (Exception ex)
            {
                Global.AddInfo($"SaveXmlConfig {xmlFile} failed. Exception: {ex.Message}");
            }
        }

        private void LoadXmlConfigByNode(XmlNode xnode)
        {
            Global.MddCount = XmlGetInt32(xnode, "MddCount", 5);
            Global.Capital = XmlGetDouble(xnode, "Capital", 100);
            Global.RiskFreeRate = XmlGetDouble(xnode, "RiskFreeRate", 3);
            Global.計算每日DD = XmlGetString(xnode, "計算每日DD", "1") == "1";
            int w = XmlGetInt32(xnode, "Width", 0);
            if (w > 0) this.Width = w;
            int h = XmlGetInt32(xnode, "Height", 0);
            if (h > 0) this.Height = h;
        }

        private void LoadXmlConfig()
        {
            string xmlFile = Path.Combine(Application.StartupPath, "VisualPortfolio.xml");
            try
            {
                if (!File.Exists(xmlFile))
                    return;

                XmlDocument xdoc = new XmlDocument();
                xdoc.Load(xmlFile);
                XmlNode xnode;
                xnode = xdoc.SelectSingleNode("/Setting");
                LoadXmlConfigByNode(xnode);
                var cfg = Global.CommissionSet.cfg;
                cfg.LoadConfig(xnode);
            }
            catch (Exception ex)
            {
                Global.AddInfo($"LoadXmlConfig {xmlFile} failed. Exception: {ex.Message}");
            }
        }

        private void tbDefaultLayout_Click(object sender, EventArgs e)
        {
            dockPanel.SuspendLayout(true);

            Global.frmSimpleSummary.DockPanel = null;
            Global.frmSimplePlot.DockPanel = null;
            Global.frmSimpleMonth.DockPanel = null;
            Global.frmEquityManage.DockPanel = null;
            Global.frmPositionAnalysis.DockPanel = null;
            Global.frmResultSummary.DockPanel = null;
            Global.frmWinLoss.DockPanel = null;
            Global.frmCommission.DockPanel = null;
            Global.frmDiversity.DockPanel = null;

            Assembly assembly = Assembly.GetAssembly(typeof(FormMain));
            Stream xmlStream = assembly.GetManifestResourceStream("VisualPortfolio.Resources.ReportPanel.xml");
            dockPanel.LoadFromXml(xmlStream, m_deserializeDockContent);
            xmlStream.Close();
            Global.frmDiversity.Show(dockPanel);

            dockPanel.ResumeLayout(true, true);
        }

        private void btnAbout_Click(object sender, EventArgs e)
        {
            FormAbout dlg = new FormAbout();
            dlg.ShowDialog();
        }
    }
}
