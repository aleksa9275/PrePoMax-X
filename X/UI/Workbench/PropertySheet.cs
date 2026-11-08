using System.ComponentModel;
using System.Globalization;

namespace PrePoMaxX.UI;

// The toolkit sees text and choices. The original PropertyDescriptor, converter,
// setters and dynamic visibility still own the property semantics.
public sealed class PropertyField
{
    public string Name {get;init;}
    public string Label {get;init;}
    public string Category {get;init;}
    public string Description {get;init;}
    public string Text {get;init;}
    public bool ReadOnly {get;init;}
    public bool Exclusive {get;init;}
    public string[] Choices {get;init;}
}
public sealed class PropertySheet
{
    readonly object instance;
    readonly Func<PropertyDescriptor,bool> filter;
    readonly Action changed;
    public PropertySheet(object value,Func<PropertyDescriptor,bool> filter=null,Action changed=null) {instance=value;this.filter=filter;this.changed=changed;}
    sealed class Context(object instance,PropertyDescriptor descriptor) : ITypeDescriptorContext
    {
        public IContainer Container=>null;
        public object Instance=>instance;
        public PropertyDescriptor PropertyDescriptor=>descriptor;
        public object GetService(Type serviceType)=>null;
        public bool OnComponentChanging()=>true;
        public void OnComponentChanged() {}
    }
    public PropertyField[] Fields => TypeDescriptor.GetProperties(instance).Cast<PropertyDescriptor>()
        .Where(p=>p.IsBrowsable && (filter==null || filter(p))).Select(p=>
        {
            var context=new Context(instance,p);
            var choices=p.Converter.GetStandardValuesSupported(context)?p.Converter.GetStandardValues(context):null;
            return new PropertyField {Name=p.Name,Label=p.DisplayName,Category=p.Category,Description=p.Description,
                Text=p.Converter.ConvertToString(context,CultureInfo.InvariantCulture,p.GetValue(instance)),
                ReadOnly=p.IsReadOnly,Exclusive=p.Converter.GetStandardValuesExclusive(context),
                Choices=choices?.Cast<object>().Select(v=>p.Converter.ConvertToString(context,CultureInfo.InvariantCulture,v)).ToArray()??[]};
        }).ToArray();
    public void Set(string name,string text)
    {
        var p=TypeDescriptor.GetProperties(instance)[name]??throw new ArgumentException("Unknown property: "+name);
        if(!p.IsBrowsable || p.IsReadOnly || (filter!=null && !filter(p)))throw new InvalidOperationException("Property is not editable: "+name);
        var context=new Context(instance,p);
        string previous=p.Converter.ConvertToString(context,CultureInfo.InvariantCulture,p.GetValue(instance));
        if(previous==text)return;
        p.SetValue(instance,p.Converter.ConvertFromString(context,CultureInfo.InvariantCulture,text));
        changed?.Invoke();
    }
}
