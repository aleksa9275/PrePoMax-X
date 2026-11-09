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
    public string Editor {get;init;}
    public bool IsFlags {get;init;}
    public bool CanConvertFromString {get;init;}
    public bool HasChildren {get;init;}
}
public sealed class PropertySheet
{
    readonly object instance;
    readonly Func<PropertyDescriptor,bool> filter;
    readonly Action changed;
    readonly Action<string> changedProperty;
    public PropertySheet(object value,Func<PropertyDescriptor,bool> filter=null,Action changed=null,Action<string> changedProperty=null) {instance=value;this.filter=filter;this.changed=changed;this.changedProperty=changedProperty;}
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
                HasChildren=p.GetValue(instance) is ICustomTypeDescriptor,ReadOnly=p.IsReadOnly,Editor=(p.Attributes[typeof(EditorAttribute)] as EditorAttribute)?.EditorTypeName,
                IsFlags=p.PropertyType.IsEnum && p.PropertyType.IsDefined(typeof(FlagsAttribute),false),CanConvertFromString=p.Converter.CanConvertFrom(context,typeof(string)),Exclusive=p.Converter.GetStandardValuesExclusive(context),
                Choices=choices?.Cast<object>().Select(v=>p.Converter.ConvertToString(context,CultureInfo.InvariantCulture,v)).ToArray()??[]};
        }).ToArray();
    public PropertySheet Child(string name)=>new((TypeDescriptor.GetProperties(instance)[name]??throw new ArgumentException(name)).GetValue(instance));
    public CollectionSheet Collection(string name)
    {
        var property=TypeDescriptor.GetProperties(instance)[name];
        return property?.GetValue(instance) is System.Collections.IList values?new CollectionSheet(values,changed):null;
    }
    public string[] CollectionNames=>TypeDescriptor.GetProperties(instance).Cast<PropertyDescriptor>().Where(p=>p.GetValue(instance) is System.Collections.IList).Select(p=>p.Name).ToArray();
    public void Set(string name,string text)
    {
        var p=TypeDescriptor.GetProperties(instance)[name]??throw new ArgumentException("Unknown property: "+name);
        if(!p.IsBrowsable || p.IsReadOnly || (filter!=null && !filter(p)))throw new InvalidOperationException("Property is not editable: "+name);
        var context=new Context(instance,p);
        string previous=p.Converter.ConvertToString(context,CultureInfo.InvariantCulture,p.GetValue(instance));
        if(previous==text)return;
        p.SetValue(instance,p.Converter.ConvertFromString(context,CultureInfo.InvariantCulture,text));
        changed?.Invoke();
        changedProperty?.Invoke(name);
    }
}
