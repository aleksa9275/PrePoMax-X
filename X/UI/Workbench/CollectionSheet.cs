using System.Collections;
using System.ComponentModel;
using CaeGlobals;
namespace PrePoMaxX.UI;

public sealed class CollectionSheet
{
    readonly IList values;
    readonly Action changed;
    readonly Func<PropertyDescriptor,bool> filter;
    public int Count=>values.Count;
    public CollectionSheet(IList values,Action changed=null,Func<PropertyDescriptor,bool> filter=null) {this.values=values;this.changed=changed;this.filter=filter;}
    public PropertySheet Row(int index)=>new(values[index],filter,changed);
    public PropertyField[] Columns=>values.Count>0?Row(0).Fields:TypeDescriptor.GetProperties(ElementType).Cast<PropertyDescriptor>().Where(p=>p.IsBrowsable && (filter==null || filter(p))).Select(p=>new PropertyField {Name=p.Name,Label=p.DisplayName,Description=p.Description,ReadOnly=p.IsReadOnly}).ToArray();
    Type ElementType=>values.GetType().GetGenericArguments().FirstOrDefault()??throw new NotSupportedException("The original collection has no element type.");
    public void Add(int after=-1)
    {
        object value=Activator.CreateInstance(ElementType);
        values.Insert(after<0?values.Count:Math.Min(values.Count,after+1),value);
        changed?.Invoke();
    }
    public void Remove(int row) {values.RemoveAt(row);changed?.Invoke();}
    public void Move(int row,int offset)
    {
        int target=row+offset;
        if(target<0 || target>=values.Count)return;
        object value=values[row];values.RemoveAt(row);values.Insert(target,value);changed?.Invoke();
    }
}
