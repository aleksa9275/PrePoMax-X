// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://github.com/PrePoMax/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

namespace vtkControl.Native
{
    // Loading on Windows, moved unchanged out of VtkNativeLibrary.cs; other platforms load the library their way
    public static partial class VtkNativeLibrary
    {
        private const string LibraryFileName = VtkNativeMethods.LibraryName;
        //
        private static IntPtr LoadModule(string path, out string reason)
        {
            IntPtr module = VtkNativeMethods.LoadLibraryEx(path, IntPtr.Zero,
                                                           VtkNativeMethods.LOAD_WITH_ALTERED_SEARCH_PATH);
            reason = module == IntPtr.Zero ? new Win32Exception(Marshal.GetLastWin32Error()).Message : null;
            return module;
        }
    }
}
