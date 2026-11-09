using CaeGlobals;using CaeMesh;using PrePoMax;using PrePoMax.Forms;
namespace PrePoMaxX.UI;
// The history prompt returns a draft to the original replay; it records no extra command.
public sealed class MeshHistoryEditSession
{
    readonly Controller controller;readonly ViewMeshSetupItem view;
    public MeshHistoryEditSession(Controller controller,MeshSetupItem item)
    {
        this.controller=controller;
        view=item is MeshingParameters mp?new ViewMeshingParameters(mp.DeepClone(),controller.Settings.Meshing.MeshingParameters.RelativeSize,mp.AdvancedView):MeshSetupItemTypes.CreateView(controller,item.DeepClone());
    }
    public PropertySheet Properties=>new(view);
    public MeshSetupItem Result {get;private set;}
    public void Apply(){var item=view.GetBase();if(item.CreationIds==null||item.CreationIds.Length==0)throw new CaeException("The mesh setup item selection must contain at least one item.");string error=controller.IsMeshSetupItemProperlyDefined(item);if(error!=null)throw new CaeException(error);Result=item;}
}
