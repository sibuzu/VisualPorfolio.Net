using System;
using System.Collections.Generic;
using System.IO;
using System.Windows.Forms;
using System.Xml;

namespace VisualPortfolio.Classes
{
    public class ClsTradeItem
    {
        public int tag, aux_idx;
        public int aux_count;
        public decimal aux_weight;
        public int idx;
        public int trade_idx;   // 記錄是那一個SRP的index
        public DateTime tradeDate1, tradeDate2;
        public decimal profit, netProfit, tradeAmount;
        public decimal contract, drawdown, drawdownPercent;
        public decimal price1, price2;
        public bool buy => bs == 'B';
        public char bs;
        public decimal pointValue;
    }

    public class ClsTradeRecord
    {
        public int strategy_index;
        public int bar_index;
        public string tag;
        public string type;
        public string symbol;
        public bool buy => bs == 'B';
        public char bs;
        public decimal contract;
        public decimal weight;
        public decimal position;
        public decimal price;
        public DateTime time_stamp;

        public ClsTradeRecord clone()
        {
            return MemberwiseClone() as ClsTradeRecord;
        }
    }

    public class ClsTradeList
    {
        private const int UNDEF = -1;
        private decimal commission = 0;

        public List<ClsTradeItem> Items = new List<ClsTradeItem>();
        public List<ClsTradeRecord> listRecord = new List<ClsTradeRecord>();
        public decimal Avg = 0, Stdev = 1;
        public long Period = 1;
        public bool Ready = false;
        public string FileName = "";
        public decimal PointValue = 1;
        public decimal NetProfit = 0;
        public decimal MDD = 0;

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
        public static int XmlGetInt32(XmlNode xn, string name, int defval = 0)
        {
            try { return Convert.ToInt32(xn.SelectSingleNode(name).InnerText); }
            catch { return defval; }
        }
        #endregion

        #region qty/price
        internal class ClsQtyPrice
        {
            internal decimal qty;
            internal decimal price;
        }

        private decimal GetQty(Dictionary<string, ClsQtyPrice> dict, string symbol)
        {
            return dict.ContainsKey(symbol) ? dict[symbol].qty : 0;
        }

        private void AddQtyPrice(Dictionary<string, ClsQtyPrice> dict, string symbol, decimal qty, decimal price)
        {
            if (dict.ContainsKey(symbol))
            {
                dict[symbol].qty += qty;
                dict[symbol].price = price;
            }
            else
            {
                ClsQtyPrice qprice = new ClsQtyPrice
                {
                    qty = qty,
                    price = price,
                };
                dict[symbol] = qprice;
            }
        }
        #endregion

        internal bool LoadPerfReport_XML(string fname)
        {
            string slippage;
            int idx = 0;
            listRecord.Clear();

            XmlDocument xdoc = new XmlDocument();
            xdoc.Load(fname);

            if (xdoc.DocumentElement.Name == "CryptoReport")
            {
                LoadXrpNode(xdoc, out slippage);
            }
            else
            {
                LoadSrpNode(xdoc, out slippage);
            }

            // sort by time, optional
            // listRecord = listRecord.OrderBy(x=>x.time_stamp).ToList();

            decimal cash = 0;

            List<ClsTradeRecord> listOpen = new List<ClsTradeRecord>();
            Dictionary<string, ClsQtyPrice> dict = new Dictionary<string, ClsQtyPrice>();
            ClsTradeItem last_item = null;
            decimal netval = 0;

            Items.Clear();

            for (int i = 0; i < listRecord.Count; ++i)
            {
                ClsTradeRecord tr = listRecord[i].clone();

                decimal qty2 = tr.contract * (tr.buy ? 1 : -1);
                decimal price = tr.price;
                string symbol = tr.symbol;
                AddQtyPrice(dict, symbol, qty2, price);

                decimal trade_amount = (tr.type == "x") ? 0 : tr.contract * tr.price * this.PointValue;
                decimal slipval = (tr.type == "x") ? 0 : util.PctOrPt(tr.price, slippage);
                if (tr.bs == 'B')
                {
                    decimal amount = tr.contract * (price + slipval) * this.PointValue;
                    cash -= amount;
                }
                else if (tr.bs == 'S')
                {
                    decimal amount = tr.contract * (price - slipval) * this.PointValue;
                    cash += amount;
                }

                decimal new_netval = cash;
                foreach (string sym in dict.Keys)
                {
                    new_netval += dict[sym].price * dict[sym].qty * this.PointValue;
                }

                ClsTradeItem item = null;
                if (last_item != null)
                {
                    double dhour = (tr.time_stamp - last_item.tradeDate1).TotalHours;
                    if (Math.Abs(dhour) < 0.5)
                    {
                        item = last_item;
                        item.profit += (new_netval - netval);
                        item.tradeAmount += trade_amount;
                        item.netProfit = item.profit;
                    }
                }
                if (item == null)
                {
                    item = new ClsTradeItem();
                    item.idx = ++idx;
                    item.tradeDate1 = tr.time_stamp;
                    item.tradeDate2 = tr.time_stamp;
                    item.price2 = tr.price;
                    item.pointValue = this.PointValue;
                    item.bs = tr.bs;
                    item.contract = tr.contract;
                    item.profit = new_netval - netval;
                    item.netProfit = item.profit;
                    item.tradeAmount = trade_amount;

                    last_item = item;
                    Items.Add(item);
                }

                netval = new_netval;
            }


            // convert to TradeItem
            this.Avg = 0; this.Stdev = 0;
            this.NetProfit = 0;
            decimal DD;
            decimal max_profit = 0;

            for (int i=0; i<Items.Count; ++i)
            {
                this.NetProfit += Items[i].profit;
                if (max_profit < this.NetProfit) max_profit = this.NetProfit;
                DD = max_profit - this.NetProfit;
                if (this.MDD < DD) this.MDD = DD;

                Avg += Items[i].profit;
                Stdev += Items[i].profit * Items[i].profit;
            }
            return true;
        }

        private void LoadSrpNode(XmlDocument xdoc, out string slippage)
        {
            decimal minPointUnit;
            decimal minPointPrice;

            #region 參數
            XmlNode xnode = xdoc.SelectSingleNode("/策略回測/參數");

            minPointUnit = XmlGetDecimal(xnode, "最小跳動點", 1);
            minPointPrice = XmlGetDecimal(xnode, "最小跳動金額", 200);
            slippage = XmlGetString(xnode, "滑價", "0");
            this.PointValue = minPointPrice / minPointUnit;
            this.NetProfit = 0;
            this.MDD = 0;
            #endregion

            Dictionary<int, decimal> StrategyPosition = new Dictionary<int, decimal>();
            xnode = xdoc.SelectSingleNode("/策略回測/策略交易");
            foreach (XmlNode xn in xnode.SelectNodes("Trade"))
            {
                ClsTradeRecord tr = new ClsTradeRecord();
                tr.strategy_index = util.GetXmlAttributeInt32(xn, "index");
                tr.bs = util.GetXmlAttributeChar(xn, "bs");
                tr.contract = util.GetXmlAttributeDecimal(xn, "contract");
                tr.price = util.GetXmlAttributeDecimal(xn, "price");
                tr.time_stamp = util.GetXmlAttributeDateTime(xn, "time_stamp");
                tr.type = util.GetXmlAttributeString(xn, "type");
                tr.symbol = util.GetXmlAttributeString(xn, "symbol", "SYM");
                if (!Global.計算每日DD && tr.type == "x") continue;

                // calc position
                decimal pos = tr.bs == 'B' ? tr.contract : tr.bs == 'S' ? -tr.contract : 0;
                if (StrategyPosition.ContainsKey(tr.strategy_index))
                    pos += StrategyPosition[tr.strategy_index];
                StrategyPosition[tr.strategy_index] = pos;
                tr.position = pos;
                listRecord.Add(tr);
            }
        }

        private void LoadXrpNode(XmlDocument xdoc, out string slippage)
        {
            #region 參數
            slippage = "0";
            this.PointValue = 1;
            this.NetProfit = 0;
            this.MDD = 0;
            #endregion

            Dictionary<int, decimal> StrategyPosition = new Dictionary<int, decimal>();
            XmlNode xnode = xdoc.SelectSingleNode("/CryptoReport/Trades");

            decimal pos = 0;
            decimal amount;
            decimal qty = 0;
            foreach (XmlNode xn in xnode.SelectNodes("Trade"))
            {
                char bs = Convert.ToChar(xn.Attributes["bs"].InnerText);

                if (bs == 'B' || bs == 'S')
                {
                    // normal trade
                    if (xn.Attributes["amount"] == null) continue;
                    amount = Convert.ToDecimal(xn.Attributes["amount"].InnerText);
                    qty = Convert.ToDecimal(xn.Attributes["qty"].InnerText);

                    ClsTradeRecord tr = new ClsTradeRecord();

                    tr.strategy_index = 0;
                    tr.bs = bs;
                    tr.contract = Math.Abs(qty);
                    tr.price = Math.Abs(amount / qty);
                    tr.time_stamp = DateTime.Parse(xn.Attributes["time_stamp"].InnerText);

                    // calc position
                    pos += tr.buy ? qty : -qty;
                    tr.position = pos;
                    listRecord.Add(tr);
                }
                else if (bs == 'N' && pos != 0)
                {
                    // empty trade
                    decimal price = Convert.ToDecimal(xn.Attributes["price"].InnerText);
                    amount = price * qty;
                    bool buy = pos < 0;

                    // trade1 
                    ClsTradeRecord tr1 = new ClsTradeRecord();
                    tr1.strategy_index = 0;
                    tr1.bs = pos > 0 ? 'S' : 'B';
                    tr1.contract = Math.Abs(pos);
                    tr1.price = price;
                    tr1.time_stamp = util.GetXmlAttributeDateTime(xn, "time_stamp");
                    tr1.position = 0;
                    listRecord.Add(tr1);

                    // trade2 
                    ClsTradeRecord tr2 = new ClsTradeRecord();
                    tr2.strategy_index = 0;
                    tr2.bs = pos > 0 ? 'B' : 'S';
                    tr2.contract = Math.Abs(pos);
                    tr2.price = price;
                    tr2.time_stamp = tr1.time_stamp;

                    // calc position
                    tr2.position = pos;
                    listRecord.Add(tr2);
                }
            }
        }

        public decimal Commission
        {
            get
            {
                if (Items.Count > 0)
                {
                    return Items[0].profit - Items[0].netProfit;
                }
                else
                {
                    return commission;
                }
            }
        }

        public void LoadFile(string fname)
        {
            bool loaded = false;
            this.Ready = false;
            this.FileName = fname;
            string ext = Path.GetExtension(fname).ToLower();

            try
            {
                this.FileName = fname;
                this.Ready = false;
                Items.Clear();

                if (!File.Exists(fname)) return;

                // TRY XML
                if (ext == ".xml" || ext == ".srp" || ext == ".xrp")
                {
                    loaded = LoadPerfReport_XML(fname);
                }

                if (!loaded)
                {
                    MessageBox.Show("The file may be not a supported TradeStration or MultiChart report");
                }

                if (Items.Count > 0)
                {
                    int n = Items.Count;
                    Avg /= n;
                    Stdev = (decimal)Math.Sqrt((double)(Stdev / n - Avg * Avg));
                    Period = (Items[Items.Count - 1].tradeDate2.Ticks - Items[0].tradeDate2.Ticks) / n + 1;

                    this.Ready = true;
                }
                else
                {
                    Avg = 0;
                    Stdev = 1;
                    Period = 1;

                    this.Ready = false;
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        #region cutdate
        internal ClsTradeList CutDate(DateTime dtStart, DateTime dtEnd)
        {
            decimal dd = 0;
            ClsTradeList lst = new ClsTradeList();
            lst.PointValue = this.PointValue;

            foreach (var ti in this.Items)
            {
                if (ti.tradeDate2 < dtStart) continue;
                if (ti.tradeDate2 > dtEnd) break;
                lst.Items.Add(ti);

                lst.NetProfit += ti.netProfit;
                dd -= ti.netProfit;
                if (dd < 0) dd = 0;
                if (lst.MDD < dd) lst.MDD = dd;
            }
            return lst;
        }
        #endregion
    }
}