using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using QuoteReader;

namespace VisualPortfolio
{
    public class TIndexDatabase
    {
        public List<QuoteEntry> listQuoteEntry = null;

        public TIndexDatabase()
        {
            _quoteType = "";
            listQuoteEntry = new List<QuoteEntry>();
        }

        private string _quoteType;
        public string QuoteType
        {
            get { return _quoteType; }
        }

        internal void Clear()
        {
            _quoteType = "";
            listQuoteEntry.Clear();
        }

        public void LoadQuoteFile(string fname, bool hideNT, int start, int end)
        {
            TQuoteReader qreader = new TQuoteReader();
            qreader.Load(fname);
            _quoteType = qreader.QuoteType;

            if (_quoteType == "TICK") return;

            int idx = listQuoteEntry.Count;
            for (int tt=0; tt<qreader.Items.Count; ++tt)
            {
                QuoteEntry qe = qreader.Items[tt];
                if (hideNT && !InTradeTime(qe.time_stamp, start, end)) continue;
                qe.index = idx++;
                listQuoteEntry.Add(qe);
            }
        }

        private bool InTradeTime(DateTime dt, int start, int end)
        {
            int t = Convert.ToInt32(dt.ToString("HHmm"));
            if (start < end)
                // same day
                return t >= start && t <= end;
            else
                // cross day
                return t >= start || t <= end;
        }

        public DateTime LastTimeStamp
        {
            get
            {
                if (listQuoteEntry.Count > 0)
                {
                    return listQuoteEntry[listQuoteEntry.Count - 1].time_stamp;
                }
                else
                {
                    return new DateTime();
                }
            }
        }

        public class QuoteEntryComparer : IComparer<QuoteEntry>
        {
            public int Compare(QuoteEntry x, QuoteEntry y)
            {
                return (x.time_stamp.CompareTo(y.time_stamp));
            }
        }

        public void CutDataSince(DateTime timeStamp)
        {
            // only the second line is lastest line
            for (int idx = listQuoteEntry.Count - 1; idx >= 0; idx--)
            {
                if (listQuoteEntry[idx].time_stamp > timeStamp)
                {
                    listQuoteEntry.RemoveAt(idx);
                }
                else
                {
                    break;
                }
            }
        }

        internal bool IsLargeTick(int i)
        {
            try
            {
                if (i == 0) return true;
                return listQuoteEntry[i].time_stamp.Day != listQuoteEntry[i - 1].time_stamp.Day;
            }
            catch (Exception)
            {
                return false;
            }
        }

        internal bool IsSmalTick(int i)
        {
            try
            {
                if (IsLargeTick(i)) return false;
                return listQuoteEntry[i].time_stamp.Hour != listQuoteEntry[i - 1].time_stamp.Hour;
            }
            catch (Exception)
            {
                return false;
            }
        }

        internal int IndexOf(DateTime timeStamp)
        {
            int low = 0;
            int high = listQuoteEntry.Count - 1;
            int mid;

            QuoteEntry ie;

            while (true)
            {
                if (low >= high)
                {
                    return low;
                }

                mid = (low + high) / 2;
                ie = listQuoteEntry[mid];

                if (ie.time_stamp < timeStamp)
                {
                    low = mid + 1;
                }
                else if (ie.time_stamp > timeStamp)
                {
                    high = mid;
                }
                else
                {
                    return mid;
                }
            }
        }

        internal static string GetPeriodStr(DateTime t1, DateTime t2)
        {
            TimeSpan ts = t2 - t1;
            string str = string.Format("{0:yyyy/MM/dd} - {1:yyyy/MM/dd}", t1, t2);
            if (ts.TotalDays > 365)
                str += string.Format(" ({0:0.0} years)", ts.TotalDays / 365);
            else if (ts.TotalDays > 60)
                str += string.Format(" ({0:0.0} months)", ts.TotalDays / 30);
            else
                str += string.Format(" ({0:0} days)", ts.TotalDays);
            return str;
        }

        internal string GetPeriodStr()
        {
            if (listQuoteEntry.Count < 2)
                return "";
            else
            {
                DateTime t1 = listQuoteEntry[0].time_stamp;
                DateTime t2 = listQuoteEntry[listQuoteEntry.Count - 1].time_stamp;
                return GetPeriodStr(t1, t2);
            }
        }
        internal double GetPeriod()
        {
            if (listQuoteEntry.Count < 2)
                return 0;
            else
            {
                DateTime t1 = listQuoteEntry[0].time_stamp;
                DateTime t2 = listQuoteEntry[listQuoteEntry.Count - 1].time_stamp;
                TimeSpan ts = t2 - t1;
                return ts.TotalDays;
            }
        }
    }
}
