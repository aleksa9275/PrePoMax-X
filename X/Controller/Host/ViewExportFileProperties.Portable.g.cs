// Generated; original property view SHA256 c44699f7ef98f7d2c079bfbf5abe33031aac6f9adce742f7eec6f1c2614fb349
using System;using System.ComponentModel;using System.Drawing.Design;using CaeGlobals;using DynamicTypeDescriptor;
namespace PrePoMax {
public sealed class CreateFileNameEditor : UITypeEditor {public static string FileName;public static string Filter;}
    [Serializable]
    public class ViewExportFileProperties
    {
        // Variables
        protected DynamicCustomTypeDescriptor _dctd = null;
        protected ExportFileProperties _properties;


        // Properties
        [CategoryAttribute("Data")]
        [OrderedDisplayName(0, 10, "File name")]
        [DescriptionAttribute("Select the file name for the exported file.")]
        [EditorAttribute(typeof(CreateFileNameEditor), typeof(UITypeEditor))]
        [Id(1, 1)]
        public string FileName { get { return _properties.FileName; } set { _properties.FileName = value; } }


        // Constructors
        public ViewExportFileProperties(ExportFileProperties exportFileProperties)
        {
            _properties = exportFileProperties;
            //
            _dctd = ProviderInstaller.Install(this);
        }


        // Methods
        public ExportFileProperties GetBase()
        {
            return _properties;
        }
        public string GetFilter()
        {
            return CreateFileNameEditor.Filter;
        }
    }
}
