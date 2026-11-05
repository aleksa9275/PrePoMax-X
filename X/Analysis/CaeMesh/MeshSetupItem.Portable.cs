// Native meshing parameter transport has no picked selection graph. The original
// selection-copy implementation remains in MeshSetupItem.Legacy.cs for Windows.
using System;
using System.Linq;
namespace CaeMesh
{
    public abstract partial class MeshSetupItem
    {
        public void CopyFrom(MeshSetupItem item)
        {
            if (item.CreationData != null)
                throw new NotSupportedException("Native meshing parameters do not copy selection graphs.");
            base.CopyFrom(item);
            _creationIds = item.CreationIds?.ToArray();
            _creationData = null;
        }
    }
}
