// Original side of the bounds comparison: the original 3.0.1 assemblies on WinForms (.NET Framework 4.8), on Windows
// or in CrossOver (see Dump.cs). Usage: PrePoMaxX.BoundsWindows.exe <PrePoMax.exe> <output.json>
using System;
using System.IO;
using System.Reflection;

namespace PrePoMaxX.Bounds
{
    public static class ProgramWindows
    {
        static string s_directory;

        [STAThread]
        public static int Main(string[] args)
        {
            if (args.Length != 2) { Console.Error.WriteLine("usage: PrePoMaxX.BoundsWindows <PrePoMax.exe> <output.json>"); return 2; }
            string exe = Path.GetFullPath(args[0]);
            s_directory = Path.GetDirectoryName(exe);
            Directory.SetCurrentDirectory(s_directory);
            AppDomain.CurrentDomain.AssemblyResolve += (sender, e) =>
            {
                string name = new AssemblyName(e.Name).Name;
                // The original keeps its assemblies in lib (probing privatePath of PrePoMax.exe.config)
                foreach (string folder in new[] { s_directory, Path.Combine(s_directory, "lib") })
                    foreach (string extension in new[] { ".dll", ".exe" })
                    {
                        string path = Path.Combine(folder, name + extension);
                        if (File.Exists(path)) return Assembly.LoadFrom(path);
                    }
                return null;
            };
            Assembly prePoMax = Assembly.LoadFrom(exe);
            string userControlsPath = Path.Combine(s_directory, "UserControls.dll");
            if (!File.Exists(userControlsPath)) userControlsPath = Path.Combine(s_directory, "lib", "UserControls.dll");
            Assembly userControls = Assembly.LoadFrom(userControlsPath);
            return Dump.Run(new[] { prePoMax, userControls }, Path.GetFullPath(args[1]),
                            "original " + prePoMax.GetName().Version + " on WinForms (.NET Framework " + Environment.Version + ")");
        }
    }
}
