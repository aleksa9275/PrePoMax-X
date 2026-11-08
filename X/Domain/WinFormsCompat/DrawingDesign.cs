// Design-time editor metadata types (System.Drawing.Design) used by the
// original DynamicTypeDescriptor/property classes. A cross-platform property
// editor can interpret these exactly like the WinForms PropertyGrid does.
using System.Collections;
using System.ComponentModel;
using System.Drawing;

namespace System.Drawing.Design
{
    public enum UITypeEditorEditStyle { None = 1, Modal = 2, DropDown = 3 }

    public class UITypeEditor
    {
        public virtual bool IsDropDownResizable => false;
        public object EditValue(IServiceProvider provider, object value) => EditValue(null, provider, value);
        public virtual object EditValue(ITypeDescriptorContext context, IServiceProvider provider, object value) => value;
        public UITypeEditorEditStyle GetEditStyle() => GetEditStyle(null);
        public virtual UITypeEditorEditStyle GetEditStyle(ITypeDescriptorContext context) => UITypeEditorEditStyle.None;
        public bool GetPaintValueSupported() => GetPaintValueSupported(null);
        public virtual bool GetPaintValueSupported(ITypeDescriptorContext context) => false;
        public void PaintValue(object value, Graphics canvas, Rectangle rectangle) =>
            PaintValue(new PaintValueEventArgs(null, value, canvas, rectangle));
        public virtual void PaintValue(PaintValueEventArgs e) { }
    }

    public class PaintValueEventArgs : EventArgs
    {
        public PaintValueEventArgs(ITypeDescriptorContext context, object value, Graphics graphics, Rectangle bounds)
        {
            Context = context; Value = value; Graphics = graphics; Bounds = bounds;
        }
        public Rectangle Bounds { get; }
        public ITypeDescriptorContext Context { get; }
        public Graphics Graphics { get; }
        public object Value { get; }
    }

    public delegate void PropertyValueUIItemInvokeHandler(ITypeDescriptorContext context, PropertyDescriptor descriptor, PropertyValueUIItem invokedItem);

    public delegate void PropertyValueUIHandler(ITypeDescriptorContext context, PropertyDescriptor propDesc, ArrayList valueUIItemList);

    public class PropertyValueUIItem
    {
        public PropertyValueUIItem(Image uiItemImage, PropertyValueUIItemInvokeHandler handler, string tooltip)
        {
            Image = uiItemImage ?? throw new ArgumentNullException(nameof(uiItemImage));
            InvokeHandler = handler ?? throw new ArgumentNullException(nameof(handler));
            ToolTip = tooltip;
        }
        public virtual Image Image { get; }
        public virtual PropertyValueUIItemInvokeHandler InvokeHandler { get; }
        public virtual string ToolTip { get; }
        public virtual void Reset() { }
    }

    public interface IPropertyValueUIService
    {
        event EventHandler PropertyUIValueItemsChanged;
        void AddPropertyValueUIHandler(PropertyValueUIHandler newHandler);
        PropertyValueUIItem[] GetPropertyUIValueItems(ITypeDescriptorContext context, PropertyDescriptor propDesc);
        void NotifyPropertyValueUIItemsChanged();
        void RemovePropertyValueUIHandler(PropertyValueUIHandler newHandler);
    }
}
