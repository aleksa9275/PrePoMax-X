// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://github.com/PrePoMax/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Text;
using System.IO;
using Microsoft.Win32;

namespace vtkControl.Native
{
    // The Windows part of the view font: the installed families and the font files of the registry
    public static partial class VtkNativeViewFont
    {
        // Variables
        private const string FontsKeyName = @"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts";


        // Methods
        // The installed families under the names the forms know
        private static List<string> GetInstalledFamilyNames()
        {
            List<string> familyNames = new List<string>();
            using (InstalledFontCollection installedFonts = new InstalledFontCollection())
            {
                foreach (FontFamily family in installedFonts.Families) familyNames.Add(family.Name);
            }
            return familyNames;
        }
        // The font files of the registry by their registered names, the per user fonts before the machine fonts
        private static Dictionary<string, string> GetRegisteredFonts()
        {
            Dictionary<string, string> registeredFonts =
                new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            string fontsFolder = Environment.GetFolderPath(Environment.SpecialFolder.Fonts);
            foreach (RegistryKey root in new RegistryKey[] { Registry.CurrentUser, Registry.LocalMachine })
            {
                using (RegistryKey key = root.OpenSubKey(FontsKeyName))
                {
                    if (key == null) continue;
                    foreach (string name in key.GetValueNames())
                    {
                        string fileName = key.GetValue(name) as string;
                        if (string.IsNullOrEmpty(fileName) || registeredFonts.ContainsKey(name)) continue;
                        registeredFonts.Add(name, Path.IsPathRooted(fileName) ? fileName
                                                                              : Path.Combine(fontsFolder, fileName));
                    }
                }
            }
            return registeredFonts;
        }
    }
}
