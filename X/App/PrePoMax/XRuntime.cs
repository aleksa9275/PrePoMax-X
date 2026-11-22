// The platform start-up of the original application on macOS and Linux (M2), before the original Program.Main:
// original PMX/settings reading through the type allowlist, executables checked by their execute permission, and
// the explicit runtime profile of this installation (PrePoMaxX.runtime.json beside PrePoMax.dll, or the file
// PREPOMAXX_RUNTIME names): the CPython 3.12 profile, the native tool manifest and the patched Gmsh library. Nothing
// is discovered through PATH; a profile that is named but invalid stops the start.
// Application.Run of the original Program shows the main form through the Avalonia front end (X/App/FrontEnd, M3-1a,
// D067) in this runtime (the M2 Qt renderer was retired in M3-1b, D065). A run with -g No - the original places its
// window off screen - runs the headless message loop instead.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Windows.Forms;
using PrePoMax;
using PrePoMax.Python;

namespace PrePoMaxX.App
{
    internal static class XRuntime
    {
        public const string FileName = "PrePoMaxX.runtime.json";

        [ModuleInitializer]
        internal static void Initialize()
        {
            // Diagnosis (opt-in): the original prints only the message of the exception that ended a run
            if (Environment.GetEnvironmentVariable("PREPOMAXX_TRACE_EXCEPTIONS") == "1")
                AppDomain.CurrentDomain.FirstChanceException += (sender, e) => Console.Error.WriteLine("[first chance] " + e.Exception);
            OriginalPersistence.Install();
            NativeTools.EnablePlatformExecutables();
            string file = Environment.GetEnvironmentVariable("PREPOMAXX_RUNTIME");
            if (string.IsNullOrEmpty(file)) file = Path.Combine(AppContext.BaseDirectory, FileName);
            else if (!Path.IsPathFullyQualified(file)) throw new ArgumentException("PREPOMAXX_RUNTIME must be an absolute path.");
            if (File.Exists(file)) Apply(file);
            Application.RunHandler = Run;
        }
        [System.Runtime.InteropServices.DllImport("libSystem.dylib")] static extern int pthread_main_np();
        /// <summary>Program -g No: StartPosition Manual at (-32000, -32000), not in the task bar (Program.Run).</summary>
        static bool IsHiddenRun(Form form) =>
            form.StartPosition == FormStartPosition.Manual && form.Location.X == -32000 && form.Location.Y == -32000 && !form.ShowInTaskbar;
        static void Run(Form mainForm)
        {
            if (IsHiddenRun(mainForm))
            {
                // On Windows the hidden window still draws its 3D view (picks, view parameters, images); here the
                // original vtkControl gets an off screen vtkNative view when FrmMain loads, before its Shown runs scripts
                mainForm.Load += (s, e) =>
                {
                    foreach (var view in Controls(mainForm).OfType<vtkControl.vtkControl>())
                    {
                        view.NativeHost.CreateOffScreenHandle();
                        view.EnableNativeMirror(true);
                    }
                };
                Application.RunHeadless(mainForm);
                return;
            }
            if (Environment.GetEnvironmentVariable("PREPOMAXX_TRACE_EXCEPTIONS") == "1")
                Console.Error.WriteLine("[run] thread " + Environment.CurrentManagedThreadId + " main " + (OperatingSystem.IsMacOS() ? pthread_main_np() : -1));
            if (Environment.GetEnvironmentVariable("PREPOMAXX_UI_PROBE") == "avalonia")
                PrePoMaxX.FrontEnd.AvaloniaFrontEnd.ProbeOutput = Environment.GetEnvironmentVariable("PREPOMAXX_UI_PROBE_OUTPUT");
            PrePoMaxX.FrontEnd.AvaloniaFrontEnd.Run(mainForm);
        }
        static IEnumerable<Control> Controls(Control control)
        {
            foreach (Control child in control.Controls)
            {
                yield return child;
                foreach (Control descendant in Controls(child)) yield return descendant;
            }
        }
        static void Apply(string file)
        {
            using JsonDocument json = JsonDocument.Parse(File.ReadAllText(file));
            JsonElement root = json.RootElement;
            if (root.GetProperty("schemaVersion").GetInt32() != 1) throw new InvalidDataException(file + ": unknown schema.");
            if (root.TryGetProperty("python", out JsonElement python)) PythonEngineManager.NativeRuntimeProfile = Absolute(python.GetString());
            if (root.TryGetProperty("nativeTools", out JsonElement tools)) NativeTools.Configure(Absolute(tools.GetString()));
            if (root.TryGetProperty("frontEnd", out JsonElement frontEnd) && frontEnd.GetString() != "avalonia")
                throw new InvalidDataException(file + ": the front end \"" + frontEnd.GetString() + "\" was retired; Avalonia is the front end.");
            // GmshCommon reads the library of the patched Gmsh from the environment (also in GmshCaller, a child process)
            if (root.TryGetProperty("gmshLibrary", out JsonElement gmsh) &&
                string.IsNullOrEmpty(Environment.GetEnvironmentVariable("PREPOMAXX_GMSH_LIBRARY")))
                Environment.SetEnvironmentVariable("PREPOMAXX_GMSH_LIBRARY", Absolute(gmsh.GetString()));
        }
        static string Absolute(string path)
        {
            if (path == null || !Path.IsPathFullyQualified(path)) throw new InvalidDataException("Runtime profile paths must be absolute: " + path);
            return path;
        }
    }
}
