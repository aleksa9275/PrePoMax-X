using CaeModel;using CaeGlobals;using PrePoMax;using PrePoMax.Forms;
namespace PrePoMaxX.UI;
public sealed class UserViewsSession(Controller controller)
{
    readonly List<UserViewParameters> views=controller.GetUserViewParameters().DeepClone();
    public string[] Names=>views.Select(v=>v.Name).ToArray();
    public PropertySheet Properties(int index)=>new(new ViewUserViewParameters(views[index]));
    public int Add(){views.Add(new UserViewParameters(Names.ToHashSet().GetNextNumberedKey("User_view")));Update(views.Count-1);return views.Count-1;}
    public void Update(int index){controller.GetViewParameters(out var position,out var focus,out var up,out double scale);var v=views[index];v.Position=position;v.FocalPoint=focus;v.UpVector=up;v.ParallelScale=scale;}
    public void Show(int index){var v=views[index];controller.SetViewParameters(true,v.Position,v.FocalPoint,v.UpVector,v.ParallelScale);}
    public void Remove(int index)=>views.RemoveAt(index);
    public void Move(int index,int delta){int target=index+delta;if(target<0||target>=views.Count)return;var v=views[index];views.RemoveAt(index);views.Insert(target,v);}
    public void Apply(){if(Names.Distinct().Count()!=views.Count)throw new CaeException("The names of user views must be unique.");controller.SetUserViewParameters(views);}
}
