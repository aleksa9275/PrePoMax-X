using System;
using System.IO;
using System.Security.Cryptography;
using System.Runtime.InteropServices;
using System.Text.Json;
using Python.Runtime;
namespace PrePoMax.Python
{
    public static partial class PythonEngineManager
    {
        // Explicit native profile; Python version/library changes are never implicit.
        public static string NativeRuntimeProfile {get;set;}
        static IntPtr pythonLibrary;
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]delegate IntPtr GetVersion();
        public static void EnsureNativeHostInitialized() {Initialize();}
        private static void ConfigurePythonRuntime()
        {
            string path=NativeRuntimeProfile;
            if(path==null || !Path.IsPathFullyQualified(path))throw new InvalidOperationException("An absolute CPython 3.12 runtime profile is required.");
            using var json=JsonDocument.Parse(File.ReadAllText(path));
            var p=json.RootElement;
            string library=p.GetProperty("library").GetString(),home=p.GetProperty("home").GetString();
            string version=p.GetProperty("version").GetString();
            if(p.GetProperty("schemaVersion").GetInt32()!=1 || !version.StartsWith("3.12.",StringComparison.Ordinal) || !Path.IsPathFullyQualified(library) || !Path.IsPathFullyQualified(home))throw new InvalidDataException("Unsupported CPython profile.");
            if(Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(library)))!=p.GetProperty("librarySha256").GetString())throw new InvalidDataException("CPython library fingerprint differs from its profile.");
            pythonLibrary=NativeLibrary.Load(library);
            string actual=Marshal.PtrToStringAnsi(Marshal.GetDelegateForFunctionPointer<GetVersion>(NativeLibrary.GetExport(pythonLibrary,"Py_GetVersion"))());
            if(!actual.StartsWith(version+" ",StringComparison.Ordinal))throw new InvalidDataException("CPython version differs from its profile: "+actual);
            Runtime.PythonDLL=library;
            PythonEngine.PythonHome=home;_pythonHome=home;
            string modules=Path.Combine(home,"lib","python3.12")+Path.PathSeparator+Path.Combine(home,"lib","python3.12","lib-dynload");
            if(p.TryGetProperty("moduleDirectories",out var directories))foreach(var d in directories.EnumerateArray())
            {
                string directory=d.GetString();
                if(!Path.IsPathFullyQualified(directory) || !Directory.Exists(directory))throw new InvalidDataException("Python module directory must exist and be absolute.");
                modules+=Path.PathSeparator+directory;
            }
            PythonEngine.PythonPath=modules;
        }
    }
}
