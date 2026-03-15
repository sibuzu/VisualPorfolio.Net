using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Xml;

namespace VisualPortfolio.Classes
{
    public class ClsBatchRun
    {
        public bool Act { get; set; }
        public int No { get; set; }
        public string Name { get; set; }
        public int Value { get; set; }
        public int Start { get; set; }
        public int Step { get; set; }
        public int End { get; set; }

        #region method
        internal bool Verified()
        {
            return End > Start;
        }

        internal int GetCount()
        {
            if (!Act) return 1;
            int p1 = Start;
            int p2 = Step;
            int p3 = End;

            if (p3 <= p1) return 1;
            else return (int)((p3 - p1) / p2) + 1;
        }

        internal void GetParameter(int idx)
        {
            if (!Act) return;
            int p1 = Start;
            int p2 = Step;
            int p3 = End;

            this.Value = p1 + p2 * idx;
        }
        #endregion
    }

    public class ClsBatchRunList : BindingList<ClsBatchRun>
    {
        internal long GetCount()
        {
            long n = 1;
            for (int i = 0; i < Count; ++i)
            {
                n *= this[i].GetCount();
            }
            return n;
        }

        internal void GetParameters(long idx)
        {
            long n;
            for (int i = Count - 1; i >= 0; --i)
            {
                n = this[i].GetCount();
                this[i].GetParameter((int) (idx % n));
                idx = idx / n;
            }
        }

        internal void GetRange(out List<decimal> lower, out List<decimal> higher)
        {
            lower = new List<decimal>();
            higher = new List<decimal>();
            for (int i = 0; i < Count; ++i)
            {
                lower.Add(0);
                higher.Add(this[i].GetCount() - 1);
            }
        }
    }

    public class ClsBatchResult
    {
        public int Index;
        public decimal 獲利 { get; set; }
        public decimal MDD { get; set; }
        [DisplayName("獲利/MDD")]
        public decimal 獲利比 { get; set; }
        public List<int> ParamValues;

        public ClsBatchResult()
        {
            ParamValues = new List<int>();
        }
    }

    public class ClsBatchResultList : List<ClsBatchResult>
    {
        public ClsBatchResultList()
        {
            ParamNames = new List<string>();
            ParamIndices = new List<int>();
        }

        public List<string> ParamNames;
        public List<int> ParamIndices;
        internal void SetParameterName(ClsBatchRunList p)
        {
            ParamNames.Clear();
            ParamIndices.Clear();
            for (int i = 0; i < p.Count; ++i)
            {
                if (p[i].GetCount() > 1)
                {
                    ParamNames.Add(p[i].Name);
                    ParamIndices.Add(i);
                }
            }
        }
    }
}
