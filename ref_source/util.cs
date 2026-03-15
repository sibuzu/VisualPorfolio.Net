using System;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Xml;
using System.Drawing;
using System.IO;
using Microsoft.Reporting.WinForms;
using System.Globalization;

namespace VisualPortfolio
{
    public class util
    {
        static public void AddElementString(XmlDocument xdoc, XmlElement elem, string name, string value)
        {
            XmlElement childElement = xdoc.CreateElement(name);
            childElement.InnerText = value;
            elem.AppendChild(childElement);
        }

        static public Int64 GetOpenContract(List<TTradeRecord> listOpen)
        {
            decimal p = 0;
            foreach (TTradeRecord tr in listOpen)
                p += tr.buy ? tr.multi : -tr.multi;
            return (Int64)p;
        }

        static public void SetGridView(DataGridView gv, List<TDetailEntry> list_detail)
        {
            gv.Columns.Clear();
            gv.AutoGenerateColumns = true;

            string[] arrList = new string[] { "No", "策略", "日期", "交易", "價格", "部位", "收益", "累計", "動作" };

            DataTable dt = new DataTable("table");
            foreach (string cname in arrList)
            {
                DataColumn dtColumn = new DataColumn();
                dtColumn.ColumnName = cname;
                dt.Columns.Add(dtColumn);
            }

            DataRow dtRow;
            foreach (TDetailEntry de in list_detail)
            {
                dtRow = dt.NewRow();
                dtRow[0] = de.index;
                dtRow[1] = de.strategy;
                dtRow[2] = de.date;
                dtRow[3] = de.trade;
                dtRow[4] = de.price;
                dtRow[5] = de.position;
                dtRow[6] = de.profit;
                dtRow[7] = de.acc_profit;
                dtRow[8] = de.action;
                dt.Rows.Add(dtRow);
            }

            gv.DataSource = new DataView(dt);
            SetGridViewStyle(gv);
        }

        static public void SetGridViewStyle(DataGridView gv)
        {
            gv.AlternatingRowsDefaultCellStyle.BackColor = Color.FromArgb(241, 245, 249);

            gv.Columns[0].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
            gv.Columns[1].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
            gv.Columns[2].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
            gv.Columns[3].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
            gv.Columns[4].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
            gv.Columns[5].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
            gv.Columns[6].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
            gv.Columns[7].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
        }


        public static void ExportTable(string fname, DataGridView dv, string encoding = "cp950")
        {
            try
            {
                var myencoding = encoding == "cp950" ? Encoding.GetEncoding(950) : Encoding.GetEncoding(encoding);
                using (StreamWriter sw = new StreamWriter(fname, false, myencoding))
                {
                    string columnHeaderText = "";

                    int countColumn = dv.ColumnCount - 1;

                    if (countColumn >= 0)
                    {
                        columnHeaderText = dv.Columns[0].HeaderText;
                    }
                    for (int i = 1; i <= countColumn; i++)
                    {
                        string s = dv.Columns[i].HeaderText;
                        s = s.Replace(",", "");
                        columnHeaderText = columnHeaderText + ',' + s;
                    }
                    sw.WriteLine(columnHeaderText);

                    foreach (DataGridViewRow dataRowObject in dv.Rows)
                    {
                        if (!dataRowObject.IsNewRow)
                        {
                            string dataFromGrid = "";

                            dataFromGrid = dataRowObject.Cells[0].Value.ToString();
                            for (int i = 1; i <= countColumn; i++)
                            {
                                string s = dataRowObject.Cells[i].Value.ToString();
                                s = s.Replace(",", "");
                                dataFromGrid = dataFromGrid + ',' + s;
                            }
                            sw.WriteLine(dataFromGrid);
                        }
                    }
                    sw.Flush();
                }
            }
            catch (Exception exceptionObject)
            {
                MessageBox.Show(exceptionObject.ToString());
            }
        }

        static internal void BindDataSource(ReportDataSourceCollection dataSources, object rlist, string name)
        {
            BindingSource bs = new BindingSource { DataSource = rlist };
            ReportDataSource ds = new ReportDataSource(name, bs);

            // Find an existing data source with the same name.
            var existingDS = dataSources.FirstOrDefault(d => d.Name == name);
            if (existingDS != null)
            {
                dataSources.Remove(existingDS);
            }

            dataSources.Add(ds);
        }

        static internal void BindDataSource(ReportViewer rv, object rlist, string name)
        {
            BindDataSource(rv.LocalReport.DataSources, rlist, name);
        }

        public static decimal PctOrPt(decimal price, string ratio_or_point)
        {
            if (ratio_or_point.Last() == '%')
            {
                decimal ratio = decimal.Parse(ratio_or_point.Substring(0, ratio_or_point.Length - 1));
                return price * ratio / 100;
            }
            else
            {
                return decimal.Parse(ratio_or_point);
            }
        }

        #region XML
        public static int GetXmlAttributeInt32(XmlNode xn, string attrName, int defval = 0)
        {
            try
            {
                var attr = xn.Attributes[attrName];
                if (attr != null)
                {
                    return int.Parse(attr.InnerText);
                }
                else
                {
                    return defval;
                }
            }
            catch (Exception ex)
            {
                return defval;
            }
        }

        public static decimal GetXmlAttributeDecimal(XmlNode xn, string attrName, decimal defval = 0)
        {
            try
            {
                var attr = xn.Attributes[attrName];
                if (attr != null)
                {
                    return decimal.Parse(attr.InnerText);
                }
                else
                {
                    return defval;
                }
            }
            catch (Exception ex)
            {
                return defval;
            }
        }

        public static DateTime GetXmlAttributeDateTime(XmlNode xn, string attrName)
        {
            try
            {
                var attr = xn.Attributes[attrName];
                if (attr != null)
                {
                    return DateTime.ParseExact(attr.InnerText,
                        "yyyy/MM/dd HH:mm:ss",
                        CultureInfo.InvariantCulture);
                }
                else
                {
                    return DateTime.MinValue;
                }
            }
            catch (Exception ex)
            {
                return DateTime.MinValue;
            }
        }

        public static char GetXmlAttributeChar(XmlNode xn, string attrName, char defval = ' ')
        {
            try
            {
                var attr = xn.Attributes[attrName];
                if (attr != null)
                {
                    return Convert.ToChar(attr.InnerText);
                }
                else
                {
                    return defval;
                }
            }
            catch (Exception ex)
            {
                return defval;
            }
        }

        public static string GetXmlAttributeString(XmlNode xn, string attrName, string defval = "")
        {
            try
            {
                var attr = xn.Attributes[attrName];
                if (attr != null)
                {
                    return attr.InnerText;
                }
                else
                {
                    return defval;
                }
            }
            catch (Exception ex)
            {
                return defval;
            }
        }
        #endregion
    }
}
