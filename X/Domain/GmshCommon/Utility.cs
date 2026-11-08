// PrePoMax-X portable port of GmshCommon/Utility.h (D062).
using System;
using System.Runtime.InteropServices;

namespace GmshCommon
{
    public class Utility
    {
        [DllImport(Gmsh.Native.Lib)]
        private static extern void gmshModelMeshGetNode(UIntPtr nodeTag, out IntPtr coord, out UIntPtr coord_n,
                                                        out IntPtr parametricCoord, out UIntPtr parametricCoord_n,
                                                        out int dim, out int tag, out int ierr);

        public static double[] GetCentroid(IntPtr elementTag, int elementType)
        {
            Gmsh.Model.Mesh.GetElement(elementTag, elementType, out IntPtr[] nodeTags, out int dim, out int tag);
            double x = 0, y = 0, z = 0;
            for (int i = 0; i < nodeTags.Length; ++i)
            {
                gmshModelMeshGetNode((UIntPtr)(ulong)nodeTags[i].ToInt64(), out IntPtr pc, out UIntPtr nc, out IntPtr pp,
                                     out UIntPtr np, out dim, out tag, out int ierr);
                Gmsh.Check(ierr);
                double[] coord = Gmsh.TakeDoubles(pc, nc);
                Gmsh.TakeDoubles(pp, np);
                x += coord[0];
                y += coord[1];
                z += coord[2];
            }
            x /= nodeTags.Length;
            y /= nodeTags.Length;
            z /= nodeTags.Length;
            return new double[] { x, y, z };
        }
    }
}
