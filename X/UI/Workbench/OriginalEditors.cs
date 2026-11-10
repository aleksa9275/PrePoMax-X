// Modal property editors of the original forms. The original UITypeEditor runs unchanged
// (PrePoMax/Selection/ItemSet/SinglePointDataEditor.cs, compiled in OriginalForms); this supplies the
// IWindowsFormsEditorService a WinForms PropertyGrid passes to it.
using System.ComponentModel;
using System.Windows.Forms;
using System.Windows.Forms.Design;

namespace PrePoMaxX.UI;

public static class OriginalEditors
{
    sealed class EditorService : IWindowsFormsEditorService, IServiceProvider
    {
        public object GetService(Type serviceType) => serviceType == typeof(IWindowsFormsEditorService) ? this : null;
        public void CloseDropDown() { }
        public void DropDownControl(Control control) { }
        public DialogResult ShowDialog(Form dialog) => dialog.ShowDialog();
    }
    /// <summary>PropertyGrid "..." on an ItemSetData point property: the original editor disables the parent
    /// form and switches the selection to node picking; the pick returns through FrmMain.PickedIds.</summary>
    public static void EditSinglePoint(PropertyGrid grid, GridItem item)
    {
        var editor = new PrePoMax.SinglePointDataEditor();
        object value = item.PropertyDescriptor.GetValue(((ITypeDescriptorContext)grid.GetContext(item)).Instance);
        object result = editor.EditValue(grid.GetContext(item), new EditorService(), value);
        if (!ReferenceEquals(result, value)) grid.SetValue(item, result);
    }
}
