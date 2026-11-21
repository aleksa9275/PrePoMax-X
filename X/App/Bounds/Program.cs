// X side of the bounds comparison: X/App's original assemblies on the FormsCompat control model (see Dump.cs)
using System;
using System.Reflection;

namespace PrePoMaxX.Bounds
{
    public static class Program
    {
        [STAThread]
        public static int Main(string[] args)
        {
            if (args.Length != 1) { Console.Error.WriteLine("usage: PrePoMaxX.Bounds <output.json>"); return 2; }
            Assembly[] assemblies = { typeof(PrePoMax.FrmMain).Assembly, typeof(UserControls.ModelTree).Assembly };
            return Dump.Run(assemblies, args[0], "X/App on FormsCompat (.NET 10)");
        }
    }
}
