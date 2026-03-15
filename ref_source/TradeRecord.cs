using System;
using System.Collections.Generic;
using System.Text;

namespace VisualPortfolio
{
    public class TTradeRecord : ICloneable
    {
        public Int64 record_index;
        public Int64 strategy_index;
        public Int64 bar_index;
        public string tag;
        public string type;
        public bool buy => bs == 'B';
        public char bs;
        public Int64 contract;
        public Int64 position;
        public decimal multi;
        public decimal price;
        public DateTime time_stamp;
        public decimal atr;

        public object Clone()
        {
            return MemberwiseClone();
        }
    }

    public class TProfitRecord
    {
        public decimal profit;
        public DateTime time_stamp;
        public Int64 open_position;
        public decimal ref_price;
        public decimal multi;
    }

    public class TimeValue
    {
        public DateTime time;
        public decimal value;
    }

}
