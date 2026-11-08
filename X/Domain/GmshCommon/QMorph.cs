// PrePoMax-X portable port of GmshCommon/QMorph.h (D062): same classes and
// members; the native QuadMesher integration is reached through the C ABI in
// native/qmorph_c.cpp (library "pmx_qmorph").
using System;
using System.Runtime.InteropServices;

namespace GmshCommon
{
    public class QMorphFaceReport
    {
        public int Tag { get; set; }
        public bool QMorph { get; set; }
        public string Reason { get; set; }
        public int Background { get; set; }
        public int Triangles { get; set; }
        public int Quads { get; set; }
        public double P95Condition { get; set; }
        public double MaxCondition { get; set; }
        public double MinAngle { get; set; }
        public double MaxAngle { get; set; }
        public double Seconds { get; set; }
        public bool Periodic { get; set; }
        public bool Singular { get; set; }
    }

    public class QMorph
    {
        private const string Lib = "pmx_qmorph";

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeReport
        {
            public int Tag, QMorph; public IntPtr Reason; public int Background, Triangles, Quads;
            public double P95Condition, MaxCondition, MinAngle, MaxAngle, Seconds; public int Periodic, Singular;
        }

        [DllImport(Lib)] private static extern void pmx_qmorph_free(IntPtr p);
        [DllImport(Lib)] private static extern int pmx_qmorph_make_face_node_counts_even(int[] tags, UIntPtr n, out int result, out IntPtr error);
        [DllImport(Lib)] private static extern int pmx_qmorph_set_background_algorithms(int[] tags, UIntPtr n, out IntPtr error);
        [DllImport(Lib)] private static extern int pmx_qmorph_quad_mesh_surfaces(int[] tags, UIntPtr n, int cleanup, int[] alternatives, UIntPtr alternatives_n, out IntPtr reports, out UIntPtr reports_n, out IntPtr error);

        private static T Call<T>(Func<T> call)
        {
            try { return call(); }
            catch (DllNotFoundException e)
            {
                throw new Exception("The Q-Morph quad mesher (QuadMesher) is not available on this platform yet: " +
                                    e.Message, e);
            }
        }
        private static void ThrowIfFailed(int status, IntPtr error)
        {
            if (status == 0) return;
            string message = Marshal.PtrToStringUTF8(error);
            pmx_qmorph_free(error);
            throw new Exception(message);
        }
        private static int[] Values(int[] values) => values ?? new int[0];

        public static int MakeFaceNodeCountsEven(int[] surfaceTags)
        {
            return Call(() =>
            {
                int[] v = Values(surfaceTags);
                ThrowIfFailed(pmx_qmorph_make_face_node_counts_even(v, (UIntPtr)v.Length, out int result, out IntPtr e), e);
                return result;
            });
        }
        public static void SetBackgroundAlgorithms(int[] surfaceTags)
        {
            Call(() =>
            {
                int[] v = Values(surfaceTags);
                ThrowIfFailed(pmx_qmorph_set_background_algorithms(v, (UIntPtr)v.Length, out IntPtr e), e);
                return 0;
            });
        }
        public static QMorphFaceReport[] QuadMeshSurfaces(int[] surfaceTags)
        {
            return QuadMeshSurfaces(surfaceTags, true, new int[] { 6, 5 });
        }
        public static QMorphFaceReport[] QuadMeshSurfaces(int[] surfaceTags, bool cleanup, int[] alternatives)
        {
            return Call(() =>
            {
                int[] v = Values(surfaceTags);
                int[] a = Values(alternatives);
                ThrowIfFailed(pmx_qmorph_quad_mesh_surfaces(v, (UIntPtr)v.Length, cleanup ? 1 : 0, a, (UIntPtr)a.Length,
                                                            out IntPtr p, out UIntPtr n, out IntPtr e), e);
                int count = (int)n;
                var result = new QMorphFaceReport[count];
                int size = Marshal.SizeOf<NativeReport>();
                for (int i = 0; i < count; i++)
                {
                    NativeReport r = Marshal.PtrToStructure<NativeReport>(p + i * size);
                    result[i] = new QMorphFaceReport
                    {
                        Tag = r.Tag, QMorph = r.QMorph != 0, Reason = Marshal.PtrToStringUTF8(r.Reason),
                        Background = r.Background, Triangles = r.Triangles, Quads = r.Quads,
                        P95Condition = r.P95Condition, MaxCondition = r.MaxCondition, MinAngle = r.MinAngle,
                        MaxAngle = r.MaxAngle, Seconds = r.Seconds, Periodic = r.Periodic != 0, Singular = r.Singular != 0
                    };
                    pmx_qmorph_free(r.Reason);
                }
                pmx_qmorph_free(p);
                return result;
            });
        }
    }
}
