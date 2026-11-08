// PrePoMax-X portable port of GmshCommon/GmshCommon.h (C++/CLI, Windows only).
//
// Same assembly, namespace, class nesting, member names, overloads and argument
// conventions as the original wrapper, so the original CaeMesh Gmsh code compiles
// unchanged (D062). Each member calls the same Gmsh 4.13 C API function that the
// original's gmsh.h (C wrapper header) called, with the same default arguments.
// Behavioural quirks of the original wrapper are kept on purpose and marked
// "Original:"; they are reviewed with the other findings after parity (D061).
using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;

namespace GmshCommon
{
    public delegate double SizeCallback(int dim, int tag, double x, double y, double z, double lc);

    public class Gmsh
    {
        // ---------------------------------------------------------------- native
        internal static class Native
        {
            internal const string Lib = "gmsh";

            // Gmsh ships as gmsh-4.13.dll / libgmsh.dylib / libgmsh.so; PREPOMAXX_GMSH_LIBRARY overrides.
            [System.Runtime.CompilerServices.ModuleInitializer]
            internal static void RegisterResolver()
            {
                NativeLibrary.SetDllImportResolver(typeof(Native).Assembly, Resolve);
            }

            private static IntPtr Resolve(string name, Assembly assembly, DllImportSearchPath? path)
            {
                if (name != Lib) return IntPtr.Zero;
                string env = Environment.GetEnvironmentVariable("PREPOMAXX_GMSH_LIBRARY");
                var candidates = new List<string>();
                if (!string.IsNullOrEmpty(env)) candidates.Add(env);
                string dir = AppContext.BaseDirectory;
                foreach (string file in new[] { "gmsh-4.13.dll", "gmsh.dll", "libgmsh.4.13.dylib", "libgmsh.dylib",
                                                "libgmsh.so.4.13", "libgmsh.so" })
                {
                    candidates.Add(Path.Combine(dir, file));
                    candidates.Add(file);
                }
                foreach (string candidate in candidates)
                {
                    if (NativeLibrary.TryLoad(candidate, assembly, path, out IntPtr handle)) return handle;
                }
                return IntPtr.Zero;
            }

            [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
            internal delegate double SizeFunction(int dim, int tag, double x, double y, double z, double lc, IntPtr data);

            [DllImport(Lib)] internal static extern void gmshFree(IntPtr p);
            [DllImport(Lib)] internal static extern void gmshInitialize(int argc, IntPtr argv, int readConfigFiles, int run, out int ierr);
            [DllImport(Lib)] internal static extern int gmshIsInitialized(out int ierr);
            [DllImport(Lib)] internal static extern void gmshFinalize(out int ierr);
            [DllImport(Lib)] internal static extern void gmshOpen([MarshalAs(UnmanagedType.LPUTF8Str)] string fileName, out int ierr);
            [DllImport(Lib)] internal static extern void gmshMerge([MarshalAs(UnmanagedType.LPUTF8Str)] string fileName, out int ierr);
            [DllImport(Lib)] internal static extern void gmshWrite([MarshalAs(UnmanagedType.LPUTF8Str)] string fileName, out int ierr);
            [DllImport(Lib)] internal static extern void gmshClear(out int ierr);
            [DllImport(Lib)] internal static extern void gmshOptionSetNumber([MarshalAs(UnmanagedType.LPUTF8Str)] string name, double value, out int ierr);
            [DllImport(Lib)] internal static extern void gmshOptionGetNumber([MarshalAs(UnmanagedType.LPUTF8Str)] string name, out double value, out int ierr);
            [DllImport(Lib)] internal static extern void gmshOptionSetString([MarshalAs(UnmanagedType.LPUTF8Str)] string name, [MarshalAs(UnmanagedType.LPUTF8Str)] string value, out int ierr);
            [DllImport(Lib)] internal static extern void gmshOptionGetString([MarshalAs(UnmanagedType.LPUTF8Str)] string name, out IntPtr value, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelAdd([MarshalAs(UnmanagedType.LPUTF8Str)] string name, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetCurrent(out IntPtr name, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelSetCurrent([MarshalAs(UnmanagedType.LPUTF8Str)] string name, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetEntities(out IntPtr dimTags, out UIntPtr dimTags_n, int dim, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelSetEntityName(int dim, int tag, [MarshalAs(UnmanagedType.LPUTF8Str)] string name, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetEntityName(int dim, int tag, out IntPtr name, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetPhysicalGroups(out IntPtr dimTags, out UIntPtr dimTags_n, int dim, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetEntitiesForPhysicalGroup(int dim, int tag, out IntPtr tags, out UIntPtr tags_n, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelAddPhysicalGroup(int dim, int[] tags, UIntPtr tags_n, int tag, [MarshalAs(UnmanagedType.LPUTF8Str)] string name, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelRemovePhysicalGroups(int[] dimTags, UIntPtr dimTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelSetPhysicalName(int dim, int tag, [MarshalAs(UnmanagedType.LPUTF8Str)] string name, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetPhysicalName(int dim, int tag, out IntPtr name, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetBoundary(int[] dimTags, UIntPtr dimTags_n, out IntPtr outDimTags, out UIntPtr outDimTags_n, int combined, int oriented, int recursive, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetAdjacencies(int dim, int tag, out IntPtr upward, out UIntPtr upward_n, out IntPtr downward, out UIntPtr downward_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetBoundingBox(int dim, int tag, out double xmin, out double ymin, out double zmin, out double xmax, out double ymax, out double zmax, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelAddDiscreteEntity(int dim, int tag, int[] boundary, UIntPtr boundary_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelRemoveEntities(int[] dimTags, UIntPtr dimTags_n, int recursive, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelSetVisibility(int[] dimTags, UIntPtr dimTags_n, int value, int recursive, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetType(int dim, int tag, out IntPtr entityType, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetValue(int dim, int tag, double[] parametricCoord, UIntPtr parametricCoord_n, out IntPtr coord, out UIntPtr coord_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetNormal(int tag, double[] parametricCoord, UIntPtr parametricCoord_n, out IntPtr normals, out UIntPtr normals_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetParametrization(int dim, int tag, double[] coord, UIntPtr coord_n, out IntPtr parametricCoord, out UIntPtr parametricCoord_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetParametrizationBounds(int dim, int tag, out IntPtr min, out UIntPtr min_n, out IntPtr max, out UIntPtr max_n, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelIsInside(int dim, int tag, double[] coord, UIntPtr coord_n, int parametric, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGetClosestPoint(int dim, int tag, double[] coord, UIntPtr coord_n, out IntPtr closestCoord, out UIntPtr closestCoord_n, out IntPtr parametricCoord, out UIntPtr parametricCoord_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelGeoSynchronize(out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelGeoAddVolume(int[] shellTags, UIntPtr shellTags_n, int tag, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelGeoAddSurfaceLoop(int[] surfaceTags, UIntPtr surfaceTags_n, int tag, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGenerate(int dim, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetSizeCallback(SizeFunction callback, IntPtr callback_data, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshRemoveSizeCallback(out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshOptimize([MarshalAs(UnmanagedType.LPUTF8Str)] string method, int force, int niter, int[] dimTags, UIntPtr dimTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshAffineTransform(double[] affineTransform, UIntPtr affineTransform_n, int[] dimTags, UIntPtr dimTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshClear(int[] dimTags, UIntPtr dimTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshAddNodes(int dim, int tag, IntPtr[] nodeTags, UIntPtr nodeTags_n, double[] coord, UIntPtr coord_n, double[] parametricCoord, UIntPtr parametricCoord_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshAddFaces(int faceType, IntPtr[] faceTags, UIntPtr faceTags_n, IntPtr[] faceNodes, UIntPtr faceNodes_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshAddElements(int dim, int tag, int[] elementTypes, UIntPtr elementTypes_n, IntPtr[] elementTags, UIntPtr[] elementTags_n, UIntPtr elementTags_nn, IntPtr[] nodeTags, UIntPtr[] nodeTags_n, UIntPtr nodeTags_nn, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshClassifySurfaces(double angle, int boundary, int forReparametrization, double curveAngle, int exportDiscrete, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshCreateGeometry(int[] dimTags, UIntPtr dimTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshCreateTopology(int makeSimplyConnected, int exportDiscrete, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGetIntegrationPoints(int elementType, [MarshalAs(UnmanagedType.LPUTF8Str)] string integrationType, out IntPtr localCoord, out UIntPtr localCoord_n, out IntPtr weights, out UIntPtr weights_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGetElementTypes(out IntPtr elementTypes, out UIntPtr elementTypes_n, int dim, int tag, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGetNodes(out IntPtr nodeTags, out UIntPtr nodeTags_n, out IntPtr coord, out UIntPtr coord_n, out IntPtr parametricCoord, out UIntPtr parametricCoord_n, int dim, int tag, int includeBoundary, int returnParametricCoord, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGetElement(UIntPtr elementTag, out int elementType, out IntPtr nodeTags, out UIntPtr nodeTags_n, out int dim, out int tag, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetNode(UIntPtr nodeTag, double[] coord, UIntPtr coord_n, double[] parametricCoord, UIntPtr parametricCoord_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGetElementProperties(int elementType, out IntPtr elementName, out int dim, out int order, out int numNodes, out IntPtr localNodeCoord, out UIntPtr localNodeCoord_n, out int numPrimaryNodes, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGetMaxNodeTag(out UIntPtr maxTag, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGetMaxElementTag(out UIntPtr maxTag, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGetElementQualities(IntPtr[] elementTags, UIntPtr elementTags_n, out IntPtr elementsQuality, out UIntPtr elementsQuality_n, [MarshalAs(UnmanagedType.LPUTF8Str)] string qualityName, UIntPtr task, UIntPtr numTasks, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGetElements(out IntPtr elementTypes, out UIntPtr elementTypes_n, out IntPtr elementTags, out IntPtr elementTags_n, out UIntPtr elementTags_nn, out IntPtr nodeTags, out IntPtr nodeTags_n, out UIntPtr nodeTags_nn, int dim, int tag, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshRemoveDuplicateNodes(int[] dimTags, UIntPtr dimTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshEmbed(int dim, int[] tags, UIntPtr tags_n, int inDim, int inTag, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshRemoveConstraints(int[] dimTags, UIntPtr dimTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshRemoveDuplicateElements(int[] dimTags, UIntPtr dimTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshRemoveElements(int dim, int tag, IntPtr[] elementTags, UIntPtr elementTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshCreateFaces(int[] dimTags, UIntPtr dimTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGetAllFaces(int faceType, out IntPtr faceTags, out UIntPtr faceTags_n, out IntPtr faceNodes, out UIntPtr faceNodes_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGetJacobians(int elementType, double[] localCoord, UIntPtr localCoord_n, out IntPtr jacobians, out UIntPtr jacobians_n, out IntPtr determinants, out UIntPtr determinants_n, out IntPtr coord, out UIntPtr coord_n, int tag, UIntPtr task, UIntPtr numTasks, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshRecombine(out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshRefine(out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetRecombine(int dim, int tag, double angle, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetAlgorithm(int dim, int tag, int val, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetSizeFromBoundary(int dim, int tag, int val, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetCompound(int dim, int[] tags, UIntPtr tags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetTransfiniteCurve(int tag, int numNodes, [MarshalAs(UnmanagedType.LPUTF8Str)] string meshType, double coef, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetTransfiniteSurface(int tag, [MarshalAs(UnmanagedType.LPUTF8Str)] string arrangement, int[] cornerTags, UIntPtr cornerTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetTransfiniteVolume(int tag, int[] cornerTags, UIntPtr cornerTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetTransfiniteAutomatic(int[] dimTags, UIntPtr dimTags_n, double cornerAngle, int recombine, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetSmoothing(int dim, int tag, int val, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetOutwardOrientation(int tag, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshSetOrder(int order, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshRenumberElements(IntPtr[] oldTags, UIntPtr oldTags_n, IntPtr[] newTags, UIntPtr newTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelMeshGetSizes(int[] dimTags, UIntPtr dimTags_n, out IntPtr sizes, out UIntPtr sizes_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccExtrude(int[] dimTags, UIntPtr dimTags_n, double dx, double dy, double dz, out IntPtr outDimTags, out UIntPtr outDimTags_n, int[] numElements, UIntPtr numElements_n, double[] heights, UIntPtr heights_n, int recombine, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccRevolve(int[] dimTags, UIntPtr dimTags_n, double x, double y, double z, double ax, double ay, double az, double angle, out IntPtr outDimTags, out UIntPtr outDimTags_n, int[] numElements, UIntPtr numElements_n, double[] heights, UIntPtr heights_n, int recombine, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccSynchronize(out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccImportShapes([MarshalAs(UnmanagedType.LPUTF8Str)] string fileName, out IntPtr outDimTags, out UIntPtr outDimTags_n, int highestDimOnly, [MarshalAs(UnmanagedType.LPUTF8Str)] string format, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccGetEntities(out IntPtr dimTags, out UIntPtr dimTags_n, int dim, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccRemove(int[] dimTags, UIntPtr dimTags_n, int recursive, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccRemoveAllDuplicates(out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccCopy(int[] dimTags, UIntPtr dimTags_n, out IntPtr outDimTags, out UIntPtr outDimTags_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccTranslate(int[] dimTags, UIntPtr dimTags_n, double dx, double dy, double dz, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelOccAddCircleArc(int startTag, int middleTag, int endTag, int tag, int center, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccDefeature(int[] volumeTags, UIntPtr volumeTags_n, int[] surfaceTags, UIntPtr surfaceTags_n, out IntPtr outDimTags, out UIntPtr outDimTags_n, int removeVolume, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccGetDistance(int dim1, int tag1, int dim2, int tag2, out double distance, out double x1, out double y1, out double z1, out double x2, out double y2, out double z2, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccFragment(int[] objectDimTags, UIntPtr objectDimTags_n, int[] toolDimTags, UIntPtr toolDimTags_n, out IntPtr outDimTags, out UIntPtr outDimTags_n, out IntPtr outDimTagsMap, out IntPtr outDimTagsMap_n, out UIntPtr outDimTagsMap_nn, int tag, int removeObject, int removeTool, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccHealShapes(out IntPtr outDimTags, out UIntPtr outDimTags_n, int[] dimTags, UIntPtr dimTags_n, double tolerance, int fixDegenerated, int fixSmallEdges, int fixSmallFaces, int sewFaces, int makeSolids, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccIntersect(int[] objectDimTags, UIntPtr objectDimTags_n, int[] toolDimTags, UIntPtr toolDimTags_n, out IntPtr outDimTags, out UIntPtr outDimTags_n, out IntPtr outDimTagsMap, out IntPtr outDimTagsMap_n, out UIntPtr outDimTagsMap_nn, int tag, int removeObject, int removeTool, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccGetMass(int dim, int tag, out double mass, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccGetCenterOfMass(int dim, int tag, out double x, out double y, out double z, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccGetEntitiesInBoundingBox(double xmin, double ymin, double zmin, double xmax, double ymax, double zmax, out IntPtr dimTags, out UIntPtr dimTags_n, int dim, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelOccAddPoint(double x, double y, double z, double meshSize, int tag, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelOccAddLine(int startTag, int endTag, int tag, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelOccAddBSpline(int[] pointTags, UIntPtr pointTags_n, int tag, int degree, double[] weights, UIntPtr weights_n, double[] knots, UIntPtr knots_n, int[] multiplicities, UIntPtr multiplicities_n, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelOccAddCurveLoop(int[] curveTags, UIntPtr curveTags_n, int tag, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelOccAddPlaneSurface(int[] wireTags, UIntPtr wireTags_n, int tag, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelOccAddBSplineSurface(int[] pointTags, UIntPtr pointTags_n, int numPointsU, int tag, int degreeU, int degreeV, double[] weights, UIntPtr weights_n, double[] knotsU, UIntPtr knotsU_n, double[] knotsV, UIntPtr knotsV_n, int[] multiplicitiesU, UIntPtr multiplicitiesU_n, int[] multiplicitiesV, UIntPtr multiplicitiesV_n, int[] wireTags, UIntPtr wireTags_n, int wire3D, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelOccAddWire(int[] curveTags, UIntPtr curveTags_n, int tag, int checkClosed, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelOccAddSurfaceLoop(int[] surfaceTags, UIntPtr surfaceTags_n, int tag, int sewing, out int ierr);
            [DllImport(Lib)] internal static extern int gmshModelOccAddVolume(int[] shellTags, UIntPtr shellTags_n, int tag, out int ierr);
            [DllImport(Lib)] internal static extern void gmshModelOccMeshSetSize(int[] dimTags, UIntPtr dimTags_n, double size, out int ierr);
            [DllImport(Lib)] internal static extern void gmshLoggerWrite([MarshalAs(UnmanagedType.LPUTF8Str)] string message, [MarshalAs(UnmanagedType.LPUTF8Str)] string level, out int ierr);
            [DllImport(Lib)] internal static extern void gmshLoggerStart(out int ierr);
            [DllImport(Lib)] internal static extern void gmshLoggerGet(out IntPtr log, out UIntPtr log_n, out int ierr);
            [DllImport(Lib)] internal static extern void gmshLoggerStop(out int ierr);
            [DllImport(Lib)] internal static extern void gmshLoggerGetLastError(out IntPtr error, out int ierr);
        }

        // --------------------------------------------------------------- helpers
        // Same behaviour as gmsh.h throwLastError(): the API error becomes an exception.
        internal static void Check(int ierr)
        {
            if (ierr == 0) return;
            Native.gmshLoggerGetLastError(out IntPtr error, out int ierr2);
            if (ierr2 != 0) throw new ExternalException("Could not get last error");
            string message = TakeString(error);
            throw new ExternalException(message);
        }
        internal static UIntPtr N(Array a) => (UIntPtr)(a == null ? 0 : a.Length);
        internal static int[] Flatten(Tuple<int, int>[] dimTags)
        {
            int[] flat = new int[dimTags.Length * 2];
            for (int i = 0; i < dimTags.Length; i++)
            {
                flat[2 * i] = dimTags[i].Item1;
                flat[2 * i + 1] = dimTags[i].Item2;
            }
            return flat;
        }
        internal static string TakeString(IntPtr p)
        {
            if (p == IntPtr.Zero) return "";
            string s = Marshal.PtrToStringUTF8(p);
            Native.gmshFree(p);
            return s;
        }
        internal static int[] TakeInts(IntPtr p, UIntPtr n)
        {
            int[] a = new int[(int)n];
            if (a.Length > 0) Marshal.Copy(p, a, 0, a.Length);
            if (p != IntPtr.Zero) Native.gmshFree(p);
            return a;
        }
        internal static double[] TakeDoubles(IntPtr p, UIntPtr n)
        {
            double[] a = new double[(int)n];
            if (a.Length > 0) Marshal.Copy(p, a, 0, a.Length);
            if (p != IntPtr.Zero) Native.gmshFree(p);
            return a;
        }
        internal static IntPtr[] TakeSizes(IntPtr p, UIntPtr n)
        {
            IntPtr[] a = new IntPtr[(int)n];
            if (a.Length > 0) Marshal.Copy(p, a, 0, a.Length);
            if (p != IntPtr.Zero) Native.gmshFree(p);
            return a;
        }
        internal static Tuple<int, int>[] TakeDimTags(IntPtr p, UIntPtr n)
        {
            int[] flat = TakeInts(p, n);
            var dimTags = new Tuple<int, int>[flat.Length / 2];
            for (int i = 0; i < dimTags.Length; i++) dimTags[i] = new Tuple<int, int>(flat[2 * i], flat[2 * i + 1]);
            return dimTags;
        }
        // size_t** + size_t* + nn, as returned by the C API (each sub-array and both outer arrays are freed)
        internal static IntPtr[][] TakeSizesArrays(IntPtr pp, IntPtr sizes, UIntPtr nn)
        {
            int count = (int)nn;
            IntPtr[] ptrs = new IntPtr[count];
            IntPtr[] lens = new IntPtr[count];
            if (count > 0)
            {
                Marshal.Copy(pp, ptrs, 0, count);
                Marshal.Copy(sizes, lens, 0, count);
            }
            var result = new IntPtr[count][];
            for (int i = 0; i < count; i++) result[i] = TakeSizes(ptrs[i], (UIntPtr)(ulong)lens[i].ToInt64());
            if (pp != IntPtr.Zero) Native.gmshFree(pp);
            if (sizes != IntPtr.Zero) Native.gmshFree(sizes);
            return result;
        }
        internal static Tuple<int, int>[][] TakeDimTagsArrays(IntPtr pp, IntPtr sizes, UIntPtr nn)
        {
            int count = (int)nn;
            IntPtr[] ptrs = new IntPtr[count];
            IntPtr[] lens = new IntPtr[count];
            if (count > 0)
            {
                Marshal.Copy(pp, ptrs, 0, count);
                Marshal.Copy(sizes, lens, 0, count);
            }
            var result = new Tuple<int, int>[count][];
            for (int i = 0; i < count; i++) result[i] = TakeDimTags(ptrs[i], (UIntPtr)(ulong)lens[i].ToInt64());
            if (pp != IntPtr.Zero) Native.gmshFree(pp);
            if (sizes != IntPtr.Zero) Native.gmshFree(sizes);
            return result;
        }
        private static readonly int[] NoInts = new int[0];
        private static readonly double[] NoDoubles = new double[0];
        private static readonly IntPtr[] NoSizes = new IntPtr[0];

        // ------------------------------------------------------- top level
        public static void Initialize()
        {
            Native.gmshInitialize(0, IntPtr.Zero, 1, 0, out int ierr); Check(ierr);
        }
        public static int IsInitialized()
        {
            int r = Native.gmshIsInitialized(out int ierr); Check(ierr); return r;
        }
        public static void FinalizeAll()
        {
            Native.gmshFinalize(out int ierr); Check(ierr);
        }
        public static void Open(string filepath)
        {
            Native.gmshOpen(filepath, out int ierr); Check(ierr);
        }
        public static void Merge(string filepath)
        {
            Native.gmshMerge(filepath, out int ierr); Check(ierr);
        }
        public static void Write(string filepath)
        {
            Native.gmshWrite(filepath, out int ierr); Check(ierr);
        }
        public static void Clear()
        {
            Native.gmshClear(out int ierr); Check(ierr);
        }

        public class Option
        {
            public static void SetNumber(string parameter, double value)
            {
                Native.gmshOptionSetNumber(parameter, value, out int ierr); Check(ierr);
            }
            public static double GetNumber(string parameter)
            {
                Native.gmshOptionGetNumber(parameter, out double value, out int ierr); Check(ierr); return value;
            }
            public static void SetString(string parameter, string value)
            {
                Native.gmshOptionSetString(parameter, value, out int ierr); Check(ierr);
            }
            public static string GetString(string parameter)
            {
                Native.gmshOptionGetString(parameter, out IntPtr value, out int ierr); Check(ierr); return TakeString(value);
            }
        }

        public class Model
        {
            public static void Add(string name)
            {
                Native.gmshModelAdd(name, out int ierr); Check(ierr);
            }
            public static string GetCurrent()
            {
                Native.gmshModelGetCurrent(out IntPtr name, out int ierr); Check(ierr); return TakeString(name);
            }
            public static void SetCurrent(string name)
            {
                Native.gmshModelSetCurrent(name, out int ierr); Check(ierr);
            }
            public static void GetEntities(out Tuple<int, int>[] dimTags)
            {
                GetEntities(out dimTags, -1);
            }
            public static void GetEntities(out Tuple<int, int>[] dimTags, int dim)
            {
                Native.gmshModelGetEntities(out IntPtr p, out UIntPtr n, dim, out int ierr); Check(ierr);
                dimTags = TakeDimTags(p, n);
            }
            public static void SetEntityName(int dim, int tag, string name)
            {
                Native.gmshModelSetEntityName(dim, tag, name, out int ierr); Check(ierr);
            }
            public static string GetEntityName(int dim, int tag)
            {
                Native.gmshModelGetEntityName(dim, tag, out IntPtr name, out int ierr); Check(ierr); return TakeString(name);
            }
            public static Tuple<int, int>[] GetPhysicalGroups(int dim)
            {
                Native.gmshModelGetPhysicalGroups(out IntPtr p, out UIntPtr n, dim, out int ierr); Check(ierr);
                return TakeDimTags(p, n);
            }
            public static int[] GetEntitiesForPhysicalGroup(int dim, int tag)
            {
                Native.gmshModelGetEntitiesForPhysicalGroup(dim, tag, out IntPtr p, out UIntPtr n, out int ierr); Check(ierr);
                return TakeInts(p, n);
            }
            public static int AddPhysicalGroup(int dim, int[] tags, string name)
            {
                return AddPhysicalGroup(dim, tags, -1, name);
            }
            public static int AddPhysicalGroup(int dim, int[] tags, int tag, string name)
            {
                int r = Native.gmshModelAddPhysicalGroup(dim, tags, N(tags), tag, name, out int ierr); Check(ierr); return r;
            }
            public static void RemovePhysicalGroups(Tuple<int, int>[] dimTags)
            {
                int[] f = Flatten(dimTags);
                Native.gmshModelRemovePhysicalGroups(f, N(f), out int ierr); Check(ierr);
            }
            public static void SetPhysicalName(int dim, int tag, string name)
            {
                Native.gmshModelSetPhysicalName(dim, tag, name, out int ierr); Check(ierr);
            }
            public static string GetPhysicalName(int dim, int tag)
            {
                Native.gmshModelGetPhysicalName(dim, tag, out IntPtr name, out int ierr); Check(ierr); return TakeString(name);
            }
            public static void GetBoundary(Tuple<int, int>[] tags, out Tuple<int, int>[] outDimTags,
                                           bool combined, bool oriented, bool recursive)
            {
                int[] f = Flatten(tags);
                Native.gmshModelGetBoundary(f, N(f), out IntPtr p, out UIntPtr n, combined ? 1 : 0, oriented ? 1 : 0,
                                            recursive ? 1 : 0, out int ierr);
                Check(ierr);
                outDimTags = TakeDimTags(p, n);
            }
            public static void GetAdjacencies(int dim, int tag, out int[] upward, out int[] downward)
            {
                Native.gmshModelGetAdjacencies(dim, tag, out IntPtr up, out UIntPtr upN, out IntPtr down, out UIntPtr downN,
                                               out int ierr);
                Check(ierr);
                upward = TakeInts(up, upN);
                downward = TakeInts(down, downN);
            }
            public static void GetBoundingBox(int dim, int tag, out double xmin, out double ymin, out double zmin,
                                              out double xmax, out double ymax, out double zmax)
            {
                Native.gmshModelGetBoundingBox(dim, tag, out xmin, out ymin, out zmin, out xmax, out ymax, out zmax,
                                               out int ierr);
                Check(ierr);
            }
            public static int AddDiscreteEntity(int dim, int tag)
            {
                int r = Native.gmshModelAddDiscreteEntity(dim, tag, NoInts, N(NoInts), out int ierr); Check(ierr); return r;
            }
            public static void RemoveEntities(Tuple<int, int>[] tags)
            {
                RemoveEntities(tags, false);
            }
            public static void RemoveEntities(Tuple<int, int>[] tags, bool recursive)
            {
                int[] f = Flatten(tags);
                Native.gmshModelRemoveEntities(f, N(f), recursive ? 1 : 0, out int ierr); Check(ierr);
            }
            public static void SetVisibility(Tuple<int, int>[] tags, int value)
            {
                SetVisibility(tags, value, false);
            }
            public static void SetVisibility(Tuple<int, int>[] tags, int value, bool recursive)
            {
                int[] f = Flatten(tags);
                Native.gmshModelSetVisibility(f, N(f), value, recursive ? 1 : 0, out int ierr); Check(ierr);
            }
            public static string GetType(int dim, int tag)
            {
                Native.gmshModelGetType(dim, tag, out IntPtr value, out int ierr); Check(ierr); return TakeString(value);
            }
            public static void GetValue(int dim, int tag, double[] parametricCoord, out double[] coord)
            {
                Native.gmshModelGetValue(dim, tag, parametricCoord, N(parametricCoord), out IntPtr p, out UIntPtr n,
                                         out int ierr);
                Check(ierr);
                coord = TakeDoubles(p, n);
            }
            public static void GetNormal(int tag, double[] parametricCoord, out double[] normals)
            {
                Native.gmshModelGetNormal(tag, parametricCoord, N(parametricCoord), out IntPtr p, out UIntPtr n, out int ierr);
                Check(ierr);
                normals = TakeDoubles(p, n);
            }
            public static void GetParametrization(int dim, int tag, double[] coord, out double[] parametricCoord)
            {
                Native.gmshModelGetParametrization(dim, tag, coord, N(coord), out IntPtr p, out UIntPtr n, out int ierr);
                Check(ierr);
                parametricCoord = TakeDoubles(p, n);
            }
            public static void GetParametrizationBounds(int dim, int tag, out double[] min, out double[] max)
            {
                Native.gmshModelGetParametrizationBounds(dim, tag, out IntPtr pMin, out UIntPtr nMin, out IntPtr pMax,
                                                         out UIntPtr nMax, out int ierr);
                Check(ierr);
                min = TakeDoubles(pMin, nMin);
                max = TakeDoubles(pMax, nMax);
            }
            public static int IsInside(int dim, int tag, double[] coord, bool parametric)
            {
                int r = Native.gmshModelIsInside(dim, tag, coord, N(coord), parametric ? 1 : 0, out int ierr); Check(ierr);
                return r;
            }
            public static void GetClosestPoint(int dim, int tag, double[] coord, out double[] closestCoord,
                                               out double[] parametricCoord)
            {
                Native.gmshModelGetClosestPoint(dim, tag, coord, N(coord), out IntPtr pc, out UIntPtr nc, out IntPtr pp,
                                                out UIntPtr np, out int ierr);
                Check(ierr);
                closestCoord = TakeDoubles(pc, nc);
                parametricCoord = TakeDoubles(pp, np);
            }

            public class Geo
            {
                public static void Synchronize()
                {
                    Native.gmshModelGeoSynchronize(out int ierr); Check(ierr);
                }
                public static int AddVolume(int[] shellTags)
                {
                    return AddVolume(shellTags, -1);
                }
                public static int AddVolume(int[] shellTags, int tag)
                {
                    int r = Native.gmshModelGeoAddVolume(shellTags, N(shellTags), tag, out int ierr); Check(ierr); return r;
                }
                public static int AddSurfaceLoop(int[] surfaceTags)
                {
                    return AddSurfaceLoop(surfaceTags, -1);
                }
                public static int AddSurfaceLoop(int[] surfaceTags, int tag)
                {
                    int r = Native.gmshModelGeoAddSurfaceLoop(surfaceTags, N(surfaceTags), tag, out int ierr); Check(ierr);
                    return r;
                }

                public class Mesh
                {
                }
            }

            public class Mesh
            {
                // Kept so that the delegate gmsh calls through is not collected while gmsh holds it
                private static SizeCallback _sizeCallback;
                private static Native.SizeFunction _sizeFunction;

                public static void Generate(int dim)
                {
                    Native.gmshModelMeshGenerate(dim, out int ierr); Check(ierr);
                }
                public static void SetSizeCallback(SizeCallback callback)
                {
                    _sizeCallback = callback;
                    _sizeFunction = (dim, tag, x, y, z, lc, data) => callback(dim, tag, x, y, z, lc);
                    Native.gmshModelMeshSetSizeCallback(_sizeFunction, IntPtr.Zero, out int ierr); Check(ierr);
                }
                public static void RemoveSizeCallback()
                {
                    Native.gmshModelMeshRemoveSizeCallback(out int ierr); Check(ierr);
                    _sizeCallback = null;
                    _sizeFunction = null;
                }
                public static void Optimize(string method, bool force, int niter, Tuple<int, int>[] dimTags)
                {
                    int[] f = Flatten(dimTags);
                    Native.gmshModelMeshOptimize(method, force ? 1 : 0, niter, f, N(f), out int ierr); Check(ierr);
                }
                public static void AffineTransform(double[] affineTransform, int[][] dimTags)
                {
                    // Original: dimTags is ignored; the transform applies to the whole mesh.
                    Native.gmshModelMeshAffineTransform(affineTransform, N(affineTransform), NoInts, N(NoInts), out int ierr);
                    Check(ierr);
                }
                public static void Clear()
                {
                    Native.gmshModelMeshClear(NoInts, N(NoInts), out int ierr); Check(ierr);
                }
                public static void Clear(Tuple<int, int>[] dimTags)
                {
                    int[] f = Flatten(dimTags);
                    Native.gmshModelMeshClear(f, N(f), out int ierr); Check(ierr);
                }
                public static void AddNodes(int dim, int tag, IntPtr[] nodeTags, double[] coordinates)
                {
                    Native.gmshModelMeshAddNodes(dim, tag, nodeTags, N(nodeTags), coordinates, N(coordinates), NoDoubles,
                                                 N(NoDoubles), out int ierr);
                    Check(ierr);
                }
                public static void AddNodes(int dim, int tag, IntPtr[] nodeTags, double[] coordinates,
                                            double[] parametricCoordinates)
                {
                    Native.gmshModelMeshAddNodes(dim, tag, nodeTags, N(nodeTags), coordinates, N(coordinates),
                                                 parametricCoordinates, N(parametricCoordinates), out int ierr);
                    Check(ierr);
                }
                public static void AddFaces(int faceType, IntPtr[] faceTags, IntPtr[] faceNodes)
                {
                    Native.gmshModelMeshAddFaces(faceType, faceTags, N(faceTags), faceNodes, N(faceNodes), out int ierr);
                    Check(ierr);
                }
                public static void AddElements(int dim, int tag, int[] elementTypes, IntPtr[][] elementTags,
                                               IntPtr[][] nodeTags)
                {
                    var handles = new List<GCHandle>();
                    try
                    {
                        IntPtr[] elementPtrs = Pin(elementTags, handles, out UIntPtr[] elementLens);
                        IntPtr[] nodePtrs = Pin(nodeTags, handles, out UIntPtr[] nodeLens);
                        Native.gmshModelMeshAddElements(dim, tag, elementTypes, N(elementTypes), elementPtrs, elementLens,
                                                        N(elementTags), nodePtrs, nodeLens, N(nodeTags), out int ierr);
                        Check(ierr);
                    }
                    finally
                    {
                        foreach (GCHandle h in handles) h.Free();
                    }
                }
                private static IntPtr[] Pin(IntPtr[][] arrays, List<GCHandle> handles, out UIntPtr[] lengths)
                {
                    IntPtr[] ptrs = new IntPtr[arrays.Length];
                    lengths = new UIntPtr[arrays.Length];
                    for (int i = 0; i < arrays.Length; i++)
                    {
                        GCHandle h = GCHandle.Alloc(arrays[i], GCHandleType.Pinned);
                        handles.Add(h);
                        ptrs[i] = h.AddrOfPinnedObject();
                        lengths[i] = (UIntPtr)arrays[i].Length;
                    }
                    return ptrs;
                }
                public static void ClassifySurfaces(double angle, bool boundary, bool forReparametrization,
                                                    double curveAngle, bool exportDiscrete)
                {
                    Native.gmshModelMeshClassifySurfaces(angle, boundary ? 1 : 0, forReparametrization ? 1 : 0, curveAngle,
                                                         exportDiscrete ? 1 : 0, out int ierr);
                    Check(ierr);
                }
                public static void CreateGeometry()
                {
                    Native.gmshModelMeshCreateGeometry(NoInts, N(NoInts), out int ierr); Check(ierr);
                }
                public static void CreateTopology()
                {
                    CreateTopology(true, true);
                }
                public static void CreateTopology(bool makeSimplyConnected, bool exportDiscrete)
                {
                    Native.gmshModelMeshCreateTopology(makeSimplyConnected ? 1 : 0, exportDiscrete ? 1 : 0, out int ierr);
                    Check(ierr);
                }
                public static void GetIntegrationPoints(int elementType, string integrationType, out double[] localCoord,
                                                        out double[] weights)
                {
                    Native.gmshModelMeshGetIntegrationPoints(elementType, integrationType, out IntPtr pc, out UIntPtr nc,
                                                             out IntPtr pw, out UIntPtr nw, out int ierr);
                    Check(ierr);
                    localCoord = TakeDoubles(pc, nc);
                    weights = TakeDoubles(pw, nw);
                }
                public static void GetElementTypes(out int[] types, int dim)
                {
                    GetElementTypes(out types, dim, -1);
                }
                public static void GetElementTypes(out int[] types)
                {
                    GetElementTypes(out types, -1, -1);
                }
                public static void GetElementTypes(out int[] types, int dim, int tag)
                {
                    Native.gmshModelMeshGetElementTypes(out IntPtr p, out UIntPtr n, dim, tag, out int ierr); Check(ierr);
                    types = TakeInts(p, n);
                }
                public static void GetNodes(out IntPtr[] nodeTags, out double[] coord, int dim, int tag,
                                            bool includeBoundary, bool returnParametricCoord)
                {
                    Native.gmshModelMeshGetNodes(out IntPtr pt, out UIntPtr nt, out IntPtr pc, out UIntPtr nc, out IntPtr pp,
                                                 out UIntPtr np, dim, tag, includeBoundary ? 1 : 0,
                                                 returnParametricCoord ? 1 : 0, out int ierr);
                    Check(ierr);
                    coord = TakeDoubles(pc, nc);
                    TakeDoubles(pp, np); // Original: parametric coordinates are not returned
                    nodeTags = TakeSizes(pt, nt);
                }
                public static void GetElement(IntPtr elementTag, int elementType, out IntPtr[] nodeTags, out int dim,
                                              out int tag)
                {
                    // Original: the elementType argument is not passed; gmsh's output value is discarded.
                    Native.gmshModelMeshGetElement((UIntPtr)(ulong)elementTag.ToInt64(), out int type, out IntPtr p,
                                                   out UIntPtr n, out dim, out tag, out int ierr);
                    Check(ierr);
                    nodeTags = TakeSizes(p, n);
                }
                public static void SetNode(IntPtr nodeTag, double[] coord, double[] parametricCoord)
                {
                    Native.gmshModelMeshSetNode((UIntPtr)(ulong)nodeTag.ToInt64(), coord, N(coord), parametricCoord,
                                                N(parametricCoord), out int ierr);
                    Check(ierr);
                }
                public static string GetElementProperties(int elementType, out int dim, out int order, out int numNodes,
                                                          out double[] localNodeCoords, out int numPrimaryNodes)
                {
                    Native.gmshModelMeshGetElementProperties(elementType, out IntPtr name, out dim, out order, out numNodes,
                                                             out IntPtr pc, out UIntPtr nc, out numPrimaryNodes, out int ierr);
                    Check(ierr);
                    localNodeCoords = TakeDoubles(pc, nc);
                    return TakeString(name);
                }
                public static void GetMaxNodeTag(out IntPtr maxTag)
                {
                    Native.gmshModelMeshGetMaxNodeTag(out UIntPtr max, out int ierr); Check(ierr);
                    maxTag = new IntPtr(unchecked((int)(ulong)max)); // Original: truncated to int
                }
                public static void GetMaxElementTag(out IntPtr maxTag)
                {
                    Native.gmshModelMeshGetMaxElementTag(out UIntPtr max, out int ierr); Check(ierr);
                    maxTag = new IntPtr(unchecked((int)(ulong)max)); // Original: truncated to int
                }
                public static void GetElementQualities(IntPtr[] elementTags, out double[] elementsQuality, string qualityName)
                {
                    Native.gmshModelMeshGetElementQualities(elementTags, N(elementTags), out IntPtr p, out UIntPtr n,
                                                            qualityName, UIntPtr.Zero, (UIntPtr)1, out int ierr);
                    Check(ierr);
                    elementsQuality = TakeDoubles(p, n);
                }
                public static void GetElements(out int[] elementTypes, out IntPtr[][] elementTags, out IntPtr[][] nodeTags,
                                               int dim, int tag)
                {
                    Native.gmshModelMeshGetElements(out IntPtr pTypes, out UIntPtr nTypes, out IntPtr pElements,
                                                    out IntPtr nElements, out UIntPtr nnElements, out IntPtr pNodes,
                                                    out IntPtr nNodes, out UIntPtr nnNodes, dim, tag, out int ierr);
                    Check(ierr);
                    elementTypes = TakeInts(pTypes, nTypes);
                    IntPtr[][] elementTagsN = TakeSizesArrays(pElements, nElements, nnElements);
                    IntPtr[][] nodeTagsN = TakeSizesArrays(pNodes, nNodes, nnNodes);
                    for (int i = 0; i < nodeTagsN.Length; i++)
                    {
                        for (int j = 0; j < nodeTagsN[i].Length; j++)
                        {
                            if (nodeTagsN[i][j] == IntPtr.Zero)
                                Console.WriteLine("Bad index found in node tags: " + nodeTagsN[i][j] + " (i " + i + ", j " + j + ")");
                        }
                    }
                    // Original: an empty result is returned as a one-element array holding null
                    elementTags = elementTagsN.Length < 1 ? new IntPtr[1][] : elementTagsN;
                    nodeTags = nodeTagsN.Length < 1 ? new IntPtr[1][] : nodeTagsN;
                }
                public static void RemoveDuplicateNodes(Tuple<int, int>[] tags)
                {
                    int[] f = Flatten(tags);
                    Native.gmshModelMeshRemoveDuplicateNodes(f, N(f), out int ierr); Check(ierr);
                }
                public static void RemoveDuplicateNodes()
                {
                    Native.gmshModelMeshRemoveDuplicateNodes(NoInts, N(NoInts), out int ierr); Check(ierr);
                }
                public static void Embed(int dim, int[] tags, int inDim, int inTag)
                {
                    Native.gmshModelMeshEmbed(dim, tags, N(tags), inDim, inTag, out int ierr); Check(ierr);
                }
                public static void RemoveConstraints(Tuple<int, int>[] dimTags)
                {
                    int[] f = Flatten(dimTags);
                    Native.gmshModelMeshRemoveConstraints(f, N(f), out int ierr); Check(ierr);
                }
                public static void RemoveDuplicateElements()
                {
                    Native.gmshModelMeshRemoveDuplicateElements(NoInts, N(NoInts), out int ierr); Check(ierr);
                }
                public static void RemoveElements(int dim, int tag)
                {
                    Native.gmshModelMeshRemoveElements(dim, tag, NoSizes, N(NoSizes), out int ierr); Check(ierr);
                }
                public static void CreateFaces()
                {
                    Native.gmshModelMeshCreateFaces(NoInts, N(NoInts), out int ierr); Check(ierr);
                }
                public static void GetAllFaces(int dim, out IntPtr[] faceTags, out IntPtr[] faceNodes)
                {
                    // Original: the argument named dim is passed as gmsh's faceType
                    Native.gmshModelMeshGetAllFaces(dim, out IntPtr pt, out UIntPtr nt, out IntPtr pn, out UIntPtr nn,
                                                    out int ierr);
                    Check(ierr);
                    faceTags = TakeSizes(pt, nt);
                    faceNodes = TakeSizes(pn, nn);
                }
                public static void GetJacobians(int elementType, int tag, double[] localCoord, out double[] jacobians,
                                                out double[] determinants, out double[] coord)
                {
                    Native.gmshModelMeshGetJacobians(elementType, localCoord, N(localCoord), out IntPtr pj, out UIntPtr nj,
                                                     out IntPtr pd, out UIntPtr nd, out IntPtr pc, out UIntPtr nc, tag,
                                                     UIntPtr.Zero, (UIntPtr)1, out int ierr);
                    Check(ierr);
                    jacobians = TakeDoubles(pj, nj);
                    determinants = TakeDoubles(pd, nd);
                    coord = TakeDoubles(pc, nc);
                }
                public static void Recombine()
                {
                    Native.gmshModelMeshRecombine(out int ierr); Check(ierr);
                }
                public static void Refine()
                {
                    Native.gmshModelMeshRefine(out int ierr); Check(ierr);
                }
                public static void SetRecombine(int dim, int tag)
                {
                    SetRecombine(dim, tag, 45.0);
                }
                public static void SetRecombine(int dim, int tag, double angle)
                {
                    Native.gmshModelMeshSetRecombine(dim, tag, angle, out int ierr); Check(ierr);
                }
                public static void SetAlgorithm(int dim, int tag, int val)
                {
                    Native.gmshModelMeshSetAlgorithm(dim, tag, val, out int ierr); Check(ierr);
                }
                public static void SetSizeFromBoundary(int dim, int tag, int val)
                {
                    Native.gmshModelMeshSetSizeFromBoundary(dim, tag, val, out int ierr); Check(ierr);
                }
                public static void SetCompound(int dim, int[] tags)
                {
                    Native.gmshModelMeshSetCompound(dim, tags, N(tags), out int ierr); Check(ierr);
                }
                public static void SetTransfiniteCurve(int tag, int numNodes)
                {
                    SetTransfiniteCurve(tag, numNodes, "Progression", 1.0);
                }
                public static void SetTransfiniteCurve(int tag, int numNodes, string meshType, double coef)
                {
                    Native.gmshModelMeshSetTransfiniteCurve(tag, numNodes, meshType, coef, out int ierr); Check(ierr);
                }
                public static void SetTransfiniteSurface(int tag)
                {
                    SetTransfiniteSurface(tag, "Left", NoInts);
                }
                public static void SetTransfiniteSurface(int tag, string arrangement)
                {
                    SetTransfiniteSurface(tag, arrangement, NoInts);
                }
                public static void SetTransfiniteSurface(int tag, string arrangement, int[] cornerTags)
                {
                    Native.gmshModelMeshSetTransfiniteSurface(tag, arrangement, cornerTags, N(cornerTags), out int ierr);
                    Check(ierr);
                }
                public static void SetTransfiniteVolume(int tag)
                {
                    SetTransfiniteVolume(tag, NoInts);
                }
                public static void SetTransfiniteVolume(int tag, int[] cornerTags)
                {
                    Native.gmshModelMeshSetTransfiniteVolume(tag, cornerTags, N(cornerTags), out int ierr); Check(ierr);
                }
                public static void SetTransfiniteAutomatic()
                {
                    SetTransfiniteAutomatic(new Tuple<int, int>[0], 2.35, true);
                }
                public static void SetTransfiniteAutomatic(double cornerAngle)
                {
                    SetTransfiniteAutomatic(new Tuple<int, int>[0], cornerAngle, true);
                }
                public static void SetTransfiniteAutomatic(double cornerAngle, bool recombine)
                {
                    SetTransfiniteAutomatic(new Tuple<int, int>[0], cornerAngle, recombine);
                }
                public static void SetTransfiniteAutomatic(Tuple<int, int>[] dimTags, double cornerAngle, bool recombine)
                {
                    int[] f = Flatten(dimTags);
                    Native.gmshModelMeshSetTransfiniteAutomatic(f, N(f), cornerAngle, recombine ? 1 : 0, out int ierr);
                    Check(ierr);
                }
                public static void SetSmoothing(int dim, int tag, int val)
                {
                    Native.gmshModelMeshSetSmoothing(dim, tag, val, out int ierr); Check(ierr);
                }
                public static void SetOutwardOrientation(int tag)
                {
                    Native.gmshModelMeshSetOutwardOrientation(tag, out int ierr); Check(ierr);
                }
                public static void SetOrder(int order)
                {
                    Native.gmshModelMeshSetOrder(order, out int ierr); Check(ierr);
                }
                public static void RenumberElements()
                {
                    Native.gmshModelMeshRenumberElements(NoSizes, N(NoSizes), NoSizes, N(NoSizes), out int ierr); Check(ierr);
                }
                public static void GetSizes(Tuple<int, int>[] dimTags, out double[] sizes)
                {
                    int[] f = Flatten(dimTags);
                    Native.gmshModelMeshGetSizes(f, N(f), out IntPtr p, out UIntPtr n, out int ierr); Check(ierr);
                    sizes = TakeDoubles(p, n);
                }

                public class Field
                {
                }
            }

            public class OCC
            {
                public static void Extrude(Tuple<int, int>[] dimTags, double dx, double dy, double dz,
                                           out Tuple<int, int>[] outDimTags, int[] numElements, double[] heights,
                                           bool recombine)
                {
                    int[] f = Flatten(dimTags);
                    Native.gmshModelOccExtrude(f, N(f), dx, dy, dz, out IntPtr p, out UIntPtr n, numElements, N(numElements),
                                               heights, N(heights), recombine ? 1 : 0, out int ierr);
                    Check(ierr);
                    outDimTags = TakeDimTags(p, n);
                }
                public static void Revolve(Tuple<int, int>[] dimTags, double x, double y, double z, double ax, double ay,
                                           double az, double angle, out Tuple<int, int>[] outDimTags, int[] numElements,
                                           double[] heights, bool recombine)
                {
                    int[] f = Flatten(dimTags);
                    Native.gmshModelOccRevolve(f, N(f), x, y, z, ax, ay, az, angle, out IntPtr p, out UIntPtr n, numElements,
                                               N(numElements), heights, N(heights), recombine ? 1 : 0, out int ierr);
                    Check(ierr);
                    outDimTags = TakeDimTags(p, n);
                }
                public static void Synchronize()
                {
                    Native.gmshModelOccSynchronize(out int ierr); Check(ierr);
                }
                public static void ImportShapes(string fileName, out Tuple<int, int>[] dimTags, bool highestDimOnly,
                                                string format)
                {
                    Native.gmshModelOccImportShapes(fileName, out IntPtr p, out UIntPtr n, highestDimOnly ? 1 : 0, format,
                                                    out int ierr);
                    Check(ierr);
                    dimTags = TakeDimTags(p, n);
                }
                public static Tuple<int, int>[] GetEntities(int dim)
                {
                    Native.gmshModelOccGetEntities(out IntPtr p, out UIntPtr n, dim, out int ierr); Check(ierr);
                    return TakeDimTags(p, n);
                }
                public static void Remove(Tuple<int, int>[] dimTags)
                {
                    Remove(dimTags, false);
                }
                public static void Remove(Tuple<int, int>[] dimTags, bool recursive)
                {
                    // Original: the native vector is created with dimTags.Length (0, 0) pairs before the
                    // requested pairs are appended, so those leading (0, 0) entries are passed too.
                    int[] f = new int[dimTags.Length * 4];
                    for (int i = 0; i < dimTags.Length; i++)
                    {
                        f[2 * (dimTags.Length + i)] = dimTags[i].Item1;
                        f[2 * (dimTags.Length + i) + 1] = dimTags[i].Item2;
                    }
                    Native.gmshModelOccRemove(f, N(f), recursive ? 1 : 0, out int ierr); Check(ierr);
                }
                public static void RemoveAllDuplicates()
                {
                    Native.gmshModelOccRemoveAllDuplicates(out int ierr); Check(ierr);
                }
                public static void Copy(Tuple<int, int>[] dimTags, out Tuple<int, int>[] outDimTags)
                {
                    int[] f = Flatten(dimTags);
                    Native.gmshModelOccCopy(f, N(f), out IntPtr p, out UIntPtr n, out int ierr); Check(ierr);
                    outDimTags = TakeDimTags(p, n);
                }
                public static void Translate(Tuple<int, int>[] dimTags, double dx, double dy, double dz)
                {
                    int[] f = Flatten(dimTags);
                    Native.gmshModelOccTranslate(f, N(f), dx, dy, dz, out int ierr); Check(ierr);
                }
                public static int AddCircleArc(int startTag, int middleTag, int endTag, bool center)
                {
                    int r = Native.gmshModelOccAddCircleArc(startTag, middleTag, endTag, -1, center ? 1 : 0, out int ierr);
                    Check(ierr);
                    return r;
                }
                public static void Defeature(int[] volumeTags, int[] surfaceTags, out Tuple<int, int>[] outDimTags,
                                             bool removeVolume)
                {
                    Native.gmshModelOccDefeature(volumeTags, N(volumeTags), surfaceTags, N(surfaceTags), out IntPtr p,
                                                 out UIntPtr n, removeVolume ? 1 : 0, out int ierr);
                    Check(ierr);
                    outDimTags = TakeDimTags(p, n);
                }
                public static void GetDistance(int dim1, int tag1, int dim2, int tag2, out double distance)
                {
                    GetDistance(dim1, tag1, dim2, tag2, out distance, out _, out _, out _, out _, out _, out _);
                }
                public static void GetDistance(int dim1, int tag1, int dim2, int tag2, out double distance, out double x1,
                                               out double y1, out double z1, out double x2, out double y2, out double z2)
                {
                    Native.gmshModelOccGetDistance(dim1, tag1, dim2, tag2, out distance, out x1, out y1, out z1, out x2,
                                                   out y2, out z2, out int ierr);
                    Check(ierr);
                }
                public static void Fragment(Tuple<int, int>[] objectDimTags, Tuple<int, int>[] toolDimTags,
                                            out Tuple<int, int>[] outDimTags, out Tuple<int, int>[][] outDimTagsMap,
                                            bool removeObject, bool removeTool)
                {
                    Fragment(objectDimTags, toolDimTags, out outDimTags, out outDimTagsMap, -1, removeObject, removeTool);
                }
                public static void Fragment(Tuple<int, int>[] objectDimTags, Tuple<int, int>[] toolDimTags,
                                            out Tuple<int, int>[] outDimTags, out Tuple<int, int>[][] outDimTagsMap, int tag,
                                            bool removeObject, bool removeTool)
                {
                    int[] o = Flatten(objectDimTags);
                    int[] t = Flatten(toolDimTags);
                    Native.gmshModelOccFragment(o, N(o), t, N(t), out IntPtr p, out UIntPtr n, out IntPtr pm, out IntPtr nm,
                                                out UIntPtr nnm, tag, removeObject ? 1 : 0, removeTool ? 1 : 0, out int ierr);
                    Check(ierr);
                    outDimTags = TakeDimTags(p, n);
                    outDimTagsMap = TakeDimTagsArrays(pm, nm, nnm);
                }
                public static void HealShapes(out Tuple<int, int>[] outDimTags, Tuple<int, int>[] dimTags, double tolerance,
                                              bool fixDegenerate, bool fixSmallEdges, bool fixSmallFaces, bool sewFaces,
                                              bool makeSolids)
                {
                    int[] f = Flatten(dimTags);
                    Native.gmshModelOccHealShapes(out IntPtr p, out UIntPtr n, f, N(f), tolerance, fixDegenerate ? 1 : 0,
                                                  fixSmallEdges ? 1 : 0, fixSmallFaces ? 1 : 0, sewFaces ? 1 : 0,
                                                  makeSolids ? 1 : 0, out int ierr);
                    Check(ierr);
                    outDimTags = TakeDimTags(p, n);
                }
                public static void Intersect(Tuple<int, int>[] objectDimTags, Tuple<int, int>[] toolDimTags,
                                             out Tuple<int, int>[] outDimTags, out Tuple<int, int>[][] outDimTagsMap, int tag,
                                             bool removeObject, bool removeTool)
                {
                    int[] o = Flatten(objectDimTags);
                    int[] t = Flatten(toolDimTags);
                    Native.gmshModelOccIntersect(o, N(o), t, N(t), out IntPtr p, out UIntPtr n, out IntPtr pm, out IntPtr nm,
                                                 out UIntPtr nnm, tag, removeObject ? 1 : 0, removeTool ? 1 : 0, out int ierr);
                    Check(ierr);
                    outDimTags = TakeDimTags(p, n);
                    outDimTagsMap = TakeDimTagsArrays(pm, nm, nnm);
                }
                public static void GetMass(int dim, int tag, out double mass)
                {
                    Native.gmshModelOccGetMass(dim, tag, out mass, out int ierr); Check(ierr);
                }
                public static void GetCenterOfMass(int dim, int tag, out double x, out double y, out double z)
                {
                    Native.gmshModelOccGetCenterOfMass(dim, tag, out x, out y, out z, out int ierr); Check(ierr);
                }
                public static void GetEntitiesInBoundingBox(double xMin, double yMin, double zMin, double xMax, double yMax,
                                                            double zMax, out Tuple<int, int>[] outDimTags, int dim)
                {
                    Native.gmshModelOccGetEntitiesInBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax, out IntPtr p,
                                                                out UIntPtr n, dim, out int ierr);
                    Check(ierr);
                    outDimTags = TakeDimTags(p, n);
                }
                public static int AddPoint(double x, double y, double z, int tag)
                {
                    return AddPoint(x, y, z, 0.0, tag);
                }
                public static int AddPoint(double x, double y, double z, double meshSize)
                {
                    return AddPoint(x, y, z, meshSize, -1);
                }
                public static int AddPoint(double x, double y, double z)
                {
                    return AddPoint(x, y, z, 0, -1);
                }
                public static int AddPoint(double x, double y, double z, double meshSize, int tag)
                {
                    int r = Native.gmshModelOccAddPoint(x, y, z, meshSize, tag, out int ierr); Check(ierr); return r;
                }
                public static int AddLine(int startTag, int endTag)
                {
                    return AddLine(startTag, endTag, -1);
                }
                public static int AddLine(int startTag, int endTag, int tag)
                {
                    int r = Native.gmshModelOccAddLine(startTag, endTag, tag, out int ierr); Check(ierr); return r;
                }
                public static int AddBSpline(int[] pointTags, int tag, int degree, double[] weights, double[] knots,
                                             int[] multiplicities)
                {
                    int r = Native.gmshModelOccAddBSpline(pointTags, N(pointTags), tag, degree, weights, N(weights), knots,
                                                          N(knots), multiplicities, N(multiplicities), out int ierr);
                    Check(ierr);
                    return r;
                }
                public static int AddBSpline(int[] pointTags, int tag, int degree, double[] weights)
                {
                    return AddBSpline(pointTags, tag, degree, weights, NoDoubles, NoInts);
                }
                public static int AddCurveLoop(int[] curveTags)
                {
                    return AddCurveLoop(curveTags, -1);
                }
                public static int AddCurveLoop(int[] curveTags, int tag)
                {
                    int r = Native.gmshModelOccAddCurveLoop(curveTags, N(curveTags), tag, out int ierr); Check(ierr); return r;
                }
                public static int AddPlaneSurface(int[] wireTags)
                {
                    return AddPlaneSurface(wireTags, -1);
                }
                public static int AddPlaneSurface(int[] wireTags, int tag)
                {
                    int r = Native.gmshModelOccAddPlaneSurface(wireTags, N(wireTags), tag, out int ierr); Check(ierr); return r;
                }
                public static int AddBSplineSurface(int[] pointTags, int numPointsU, int tag, int degreeU, int degreeV,
                                                    double[] weights, double[] knotsU, double[] knotsV, int[] multiplicitiesU,
                                                    int[] multiplicitiesV, int[] wireTags, bool wire3d)
                {
                    int r = Native.gmshModelOccAddBSplineSurface(pointTags, N(pointTags), numPointsU, tag, degreeU, degreeV,
                                                                 weights, N(weights), knotsU, N(knotsU), knotsV, N(knotsV),
                                                                 multiplicitiesU, N(multiplicitiesU), multiplicitiesV,
                                                                 N(multiplicitiesV), wireTags, N(wireTags), wire3d ? 1 : 0,
                                                                 out int ierr);
                    Check(ierr);
                    return r;
                }
                public static int AddBSplineSurface(int[] pointTags, int numPointsU, int tag, int degreeU, int degreeV,
                                                    double[] weights, int[] wireTags, bool wire3d)
                {
                    return AddBSplineSurface(pointTags, numPointsU, tag, degreeU, degreeV, weights, NoDoubles, NoDoubles,
                                             NoInts, NoInts, wireTags, wire3d);
                }
                public static int AddBSplineSurface(int[] pointTags, int numPointsU, int tag, int degreeU, int degreeV,
                                                    double[] weights)
                {
                    return AddBSplineSurface(pointTags, numPointsU, tag, degreeU, degreeV, weights, NoDoubles, NoDoubles,
                                             NoInts, NoInts, NoInts, false);
                }
                public static int AddWire(int[] curveTags, int tag, bool checkClosed)
                {
                    int r = Native.gmshModelOccAddWire(curveTags, N(curveTags), tag, checkClosed ? 1 : 0, out int ierr);
                    Check(ierr);
                    return r;
                }
                public static int AddSurfaceLoop(int[] surfaceTags)
                {
                    return AddSurfaceLoop(surfaceTags, -1);
                }
                public static int AddSurfaceLoop(int[] surfaceTags, int tag)
                {
                    int r = Native.gmshModelOccAddSurfaceLoop(surfaceTags, N(surfaceTags), tag, 0, out int ierr); Check(ierr);
                    return r;
                }
                public static int AddVolume(int[] shellTags)
                {
                    return AddVolume(shellTags, -1);
                }
                public static int AddVolume(int[] shellTags, int tag)
                {
                    int r = Native.gmshModelOccAddVolume(shellTags, N(shellTags), tag, out int ierr); Check(ierr); return r;
                }
                public static void SetSize(Tuple<int, int>[] dimTags, double size)
                {
                    int[] f = Flatten(dimTags);
                    Native.gmshModelOccMeshSetSize(f, N(f), size, out int ierr); Check(ierr);
                }

                public class Mesh
                {
                }
            }
        }

        public class Logger
        {
            public static void Write(string message, string level)
            {
                Native.gmshLoggerWrite(message, level, out int ierr); Check(ierr);
            }
            public static void Start()
            {
                Native.gmshLoggerStart(out int ierr); Check(ierr);
            }
            public static string[] Get()
            {
                Native.gmshLoggerGet(out IntPtr p, out UIntPtr n, out int ierr); Check(ierr);
                int count = (int)n;
                IntPtr[] ptrs = new IntPtr[count];
                if (count > 0) Marshal.Copy(p, ptrs, 0, count);
                string[] log = new string[count];
                for (int i = 0; i < count; i++) log[i] = TakeString(ptrs[i]);
                if (p != IntPtr.Zero) Native.gmshFree(p);
                return log;
            }
            public static void Stop()
            {
                Native.gmshLoggerStop(out int ierr); Check(ierr);
            }
            public static string GetLastError()
            {
                Native.gmshLoggerGetLastError(out IntPtr error, out int ierr); Check(ierr); return TakeString(error);
            }
        }
    }
}
