// PrePoMax-X: loading of the native view library on macOS and Linux (and in the X build on Windows).
// The DllImport declarations of the original code name "vtkNative.dll"; the resolver binds them to the module
// loaded here by its full path, beside the vtkControl assembly, as the original loads vtkNative.dll there.
using System;
using System.Runtime.InteropServices;

namespace vtkControl.Native
{
    public static partial class VtkNativeLibrary
    {
        private static readonly string LibraryFileName =
            OperatingSystem.IsWindows() ? VtkNativeMethods.LibraryName :
            OperatingSystem.IsMacOS() ? "libvtkNative.dylib" : "libvtkNative.so";
        //
        private static IntPtr LoadModule(string path, out string reason)
        {
            reason = null;
            try
            {
                IntPtr module = NativeLibrary.Load(path);
                NativeLibrary.SetDllImportResolver(typeof(VtkNativeLibrary).Assembly, (name, assembly, searchPath) =>
                    name == VtkNativeMethods.LibraryName ? module : IntPtr.Zero);
                return module;
            }
            catch (Exception exception) when (exception is DllNotFoundException || exception is BadImageFormatException ||
                                              exception is InvalidOperationException)
            {
                reason = exception.Message;
                return IntPtr.Zero;
            }
        }
    }
}
