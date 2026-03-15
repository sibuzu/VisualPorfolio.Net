using System.ComponentModel;

namespace VisualPortfolio.Classes
{
    public class ClsListEquity : BindingList<ClsEquityAttr>
    {
        public ClsListEquity()
        {
            DivByCount = false;
        }

        public bool DivByCount { get; internal set; }
        public double ContractFactor
        {
            get
            {
                if (DivByCount)
                {
                    int n = 0;
                    foreach (var elm in this)
                    {
                        if (elm.Active) n += elm.Contract;
                    }
                    return n == 0 ? 1.0 : 1.0 / n;
                }
                else
                {
                    return 1;
                }
            }
        }

        internal void RemoveEntry(int idx)
        {
            this.RemoveAt(idx);
            // this.ResetIndex();
        }

        internal void ResetIndex()
        {
            for (int i = 0; i < this.Count; ++i)
            {
                this[i].Index = i + 1;
                foreach (var te in this.Items[i].TradeList.Items)
                    te.trade_idx = i + 1;
            }
        }

        internal int MoveUp(int idx)
        {
            if (idx <= 0 || idx >= this.Count) return idx;

            var tmp = this[idx];
            this[idx]= this[idx - 1];
            this[idx - 1] = tmp;

            return idx - 1;
        }

        internal int MoveDown(int idx)
        {
            if (idx < 0 || idx >= this.Count - 1) return idx;

            var tmp = this[idx];
            this[idx] = this[idx + 1];
            this[idx + 1] = tmp;

            return idx + 1;
        }
    }
}
