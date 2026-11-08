// PrePoMax-X portable counterpart of CaeGlobals/DynamicTypeDescriptor/
// DynamicTypeDescriptor.WinForms.cs (D062). It carries the same editor metadata
// (drop-down, resizable); the cross-platform property editor builds the
// drop-down from the property's standard values.
using System;
using System.ComponentModel;
using System.Drawing.Design;

namespace DynamicTypeDescriptor
{
    public class StandardValueEditor : UITypeEditor
    {
        public override bool GetPaintValueSupported(ITypeDescriptorContext context) => false;
        public override UITypeEditorEditStyle GetEditStyle(ITypeDescriptorContext context) => UITypeEditorEditStyle.DropDown;
        public override bool IsDropDownResizable => true;
        public override object EditValue(ITypeDescriptorContext context, IServiceProvider provider, object value) => value;
    }
}
