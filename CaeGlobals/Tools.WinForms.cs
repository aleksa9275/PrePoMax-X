// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://github.com/PrePoMax/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

// PrePoMax-X: the application start-up folder (WinForms) and the Windows short
// path API, moved from Tools.cs (D062). The portable build supplies
// X/Domain/CaeGlobals/Portable/Tools.Portable.cs.

using System.Runtime.InteropServices;
using System.Text;

namespace CaeGlobals
{
    public static partial class Tools
    {
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern uint GetShortPathName(string longPath, StringBuilder shortPath, uint bufferLength);
        private static string GetApplicationRelativePath(string path)
        {
            return System.IO.Path.Combine(StartupPath, path.TrimStart('\\'));
        }
        private static string StartupPath
        {
            get { return System.Windows.Forms.Application.StartupPath; }
        }
    }
}
