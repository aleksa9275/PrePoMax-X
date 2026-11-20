// M3-1 toolkit spike (D065): the original Program.Main of X/App with Avalonia as the front end, in one .NET runtime.
// XRuntime (the module initializer of PrePoMax.dll) reads the runtime profile and installs its Qt handler; this
// replaces Application.RunHandler with the Avalonia one before the original Main runs.
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Themes.Fluent;
using WinForms = System.Windows.Forms;

namespace PrePoMaxX.FrontEndSpike
{
    internal static class Program
    {
        [STAThread]
        static int Main(string[] args)
        {
            // PrePoMax.Program is internal to the original assembly
            Type program = Type.GetType("PrePoMax.Program, PrePoMax", throwOnError: true);
            RuntimeHelpers.RunModuleConstructor(program.Module.ModuleHandle);
            WinForms.Application.RunHandler = FrontEnd.Run;
            MethodInfo main = program.GetMethod("Main", BindingFlags.Static | BindingFlags.NonPublic | BindingFlags.Public);
            try { main.Invoke(null, new object[] { args }); }
            catch (TargetInvocationException e) { Console.Error.WriteLine(e.InnerException); return 1; }
            return Environment.ExitCode;
        }
    }

    internal sealed class SpikeApplication : Application
    {
        internal static WinForms.Form MainForm;
        public override void Initialize() { Styles.Add(new FluentTheme()); RequestedThemeVariant = Avalonia.Styling.ThemeVariant.Light; }
        public override void OnFrameworkInitializationCompleted()
        {
            if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
            {
                FrontEnd.StartMessageQueue();
                desktop.MainWindow = new FormWindow(MainForm, FrontEnd.Context, true);
            }
            base.OnFrameworkInitializationCompleted();
        }
    }
}
