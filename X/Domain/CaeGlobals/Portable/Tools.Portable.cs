// PrePoMax-X portable counterpart of CaeGlobals/Tools.WinForms.cs (D062).
// StartupPath matches WinForms Application.StartupPath: the executable's folder
// without a trailing separator. macOS/Linux have no 8.3 short names, so the short
// path query reports "none" and the original caller keeps the full path.
using System;
using System.IO;
using System.Text;

namespace CaeGlobals
{
    public static partial class Tools
    {
        private static uint GetShortPathName(string longPath, StringBuilder shortPath, uint bufferLength)
        {
            return 0;
        }
        private static string StartupPath
        {
            get { return Path.TrimEndingDirectorySeparator(AppContext.BaseDirectory); }
        }
    }
}
