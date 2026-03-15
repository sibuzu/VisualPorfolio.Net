using System;
using System.ComponentModel;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Xml;
using System.Xml.Serialization;

namespace VisualPortfolio
{
    public interface IUpdateUIVisibily
    {
        void UpdatePropertyGrid();
    }

    public class ClsNotify : INotifyPropertyChanged
    {
        #region INotifyPropertyChanged
        public event PropertyChangedEventHandler PropertyChanged = delegate { };

        public virtual void RaisePropertyChanged([CallerMemberName] string name = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }
        #endregion
    }

    public class ClsProperty : ClsNotify
    {
        #region UI Visibility
        [Browsable(false), XmlIgnore]
        public IUpdateUIVisibily UIObject;

        public virtual void ChangePropertyVisibility()
        {
        }

        public void UpdateUIVisibility()
        {
            ChangePropertyVisibility();
            UIObject?.UpdatePropertyGrid();
        }
        #endregion

        #region Config
        public virtual void LoadConfig(XmlNode xnode)
        {
            try
            {
                XmlNode xn = xnode.SelectSingleNode(this.GetType().Name);
                if (xn != null)
                {
                    var serializer = new XmlSerializer(this.GetType());
                    ClsProperty st = serializer.Deserialize(new XmlNodeReader(xn)) as ClsProperty;
                    this.CopyFrom(st);
                }
            }
            catch (Exception ex)
            {
                Global.AddInfo($"Load {this.GetType().Name} config failed. Exception: {ex.Message}");
            }
        }

        public virtual void SaveConfig(XmlWriter writer)
        {
            try
            {
                XmlSerializerNamespaces ns = new XmlSerializerNamespaces();
                ns.Add("", "");
                var serializer = new XmlSerializer(this.GetType());
                serializer.Serialize(writer, this, ns);
            }
            catch (Exception ex)
            {
                Global.AddInfo($"Save {this.GetType().Name} config failed. Exception: {ex.Message}");
            }
        }

        public object Clone()
        {
            return this.MemberwiseClone();
        }

        public void CopyFrom(ClsProperty src)
        {
            PropertyInfo[] infos = this.GetType().GetProperties();
            foreach (PropertyInfo info in infos)
            {
                if (info.CanWrite)
                    info.SetValue(this, info.GetValue(src, null), null);
            }
        }
        #endregion
    }

    public class PropertyChangedPropagator
    {
        public static PropertyChangedEventHandler Create(string sourcePropertyName, string dependantPropertyName, Action<string> raisePropertyChanged)
        {
            var infiniteRecursionDetected = false;
            return (sender, args) =>
            {
                try
                {
                    if (args.PropertyName != sourcePropertyName) return;
                    if (infiniteRecursionDetected)
                    {
                        throw new InvalidOperationException("Infinite recursion detected");
                    }
                    infiniteRecursionDetected = true;
                    raisePropertyChanged(dependantPropertyName);
                }
                finally
                {
                    infiniteRecursionDetected = false;
                }
            };
        }
    }

}
