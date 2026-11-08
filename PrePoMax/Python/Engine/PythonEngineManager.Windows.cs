using System.IO;
using System.Windows.Forms;
using Python.Runtime;
namespace PrePoMax.Python { public static partial class PythonEngineManager {
        private static void ConfigurePythonRuntime()
        {
            string pythonDll = Application.StartupPath + Globals.PythonDll;
            string pythonDir = Path.GetDirectoryName(pythonDll);
            //
            if (!File.Exists(pythonDll))
                throw new FileNotFoundException("Python DLL was not found.", pythonDll);
            //
            Runtime.PythonDLL = pythonDll;
            // Help Python find its standard library and extension modules.
            PythonEngine.PythonHome = pythonDir;
            _pythonHome = pythonDir;
            PythonEngine.PythonPath = Path.Combine(pythonDir, "Lib") + Path.PathSeparator +
                                      Path.Combine(pythonDir, "DLLs") + Path.PathSeparator +
                                      Path.Combine(pythonDir, "Lib", "site-packages");
        }
}}
