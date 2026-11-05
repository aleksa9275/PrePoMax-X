// Original selection-copy orchestration retained in the Windows assembly.
using System.Linq;
namespace CaeMesh
{
    public abstract partial class MeshSetupItem
    {
        public void CopyFrom(MeshSetupItem meshSetupItem)
        {
            base.CopyFrom(meshSetupItem);
            //
            _creationIds = meshSetupItem.CreationIds?.ToArray();
            _creationData = meshSetupItem.CreationData?.DeepCopy(true, false);
        }
    }
}
