// Generated; original property view SHA256 eecc80b636a5b93b443a1c58b7c121c2d29c8347281051813a2a58f0e643f6a8
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
