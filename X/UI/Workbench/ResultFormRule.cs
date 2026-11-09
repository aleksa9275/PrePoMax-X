using CaeGlobals;using PrePoMax;
namespace PrePoMaxX.UI.OriginalForms;
public abstract class ResultFormRule(Controller controller,string name):FormRule(controller,null,name)
{
 public override string[] CollectionNames=>Item is CaeResults.ResultHistoryOutputFromTable?[]:base.CollectionNames;
 public override PropertySheet Properties=>new(View,changedProperty:PropertyChanged);
 protected virtual void PropertyChanged(string property)=>Changed();
 public override string[] SelectionPrefixes=>[];
 public virtual vtkSelectItem SelectionKind=>vtkSelectItem.None;
 public void PrepareSelection(){_controller.ClearAllSelection();_controller.SetSelectItemToNode();_controller.SelectItem=SelectionKind;}
 public override void SetSelection(int[] ids,Selection source=null,string prefix="")
 {
  if(source==null || source.CurrentView!=(int)ViewGeometryModelResults.Results || source.SelectItem!=SelectionKind)throw new CaeException("Pick the requested result region first.");
  base.SetSelection(ids,source,prefix);
 }
 public System.Threading.Tasks.Task CommitInBackground()=>System.Threading.Tasks.Task.Run(Commit);
}
