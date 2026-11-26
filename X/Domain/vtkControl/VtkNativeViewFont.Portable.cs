// PrePoMax-X: the font files of the view text on macOS and Linux, in place of vtkControl's VtkNativeViewFont.Windows.cs.
// Windows lists its fonts in the registry as "<family>[ <style>] (TrueType|OpenType)" -> file; the same names are
// read here from the name table of every .ttf and .otf file in the system and user font folders, so the original
// lookup (FindFontFiles) runs unchanged. Font collections (.ttc) are left out, as the original leaves them out.
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace vtkControl.Native
{
    public static partial class VtkNativeViewFont
    {
        private static readonly object PortableFontsLock = new object();
        private static Dictionary<string, string> _portableFonts;
        private static List<string> _portableFamilyNames;

        private static List<string> GetInstalledFamilyNames()
        {
            ScanPortableFonts();
            return new List<string>(_portableFamilyNames);
        }

        private static Dictionary<string, string> GetRegisteredFonts()
        {
            ScanPortableFonts();
            return new Dictionary<string, string>(_portableFonts, StringComparer.OrdinalIgnoreCase);
        }

        // The user folders before the system folders, as the registry lists per user fonts first
        private static IEnumerable<string> GetFontFolders()
        {
            string home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            if (OperatingSystem.IsMacOS())
            {
                yield return Path.Combine(home, "Library", "Fonts");
                yield return "/Library/Fonts";
                yield return "/System/Library/Fonts";
            }
            else
            {
                string dataHome = Environment.GetEnvironmentVariable("XDG_DATA_HOME");
                if (string.IsNullOrEmpty(dataHome)) dataHome = Path.Combine(home, ".local", "share");
                yield return Path.Combine(dataHome, "fonts");
                yield return Path.Combine(home, ".fonts");
                yield return "/usr/local/share/fonts";
                yield return "/usr/share/fonts";
            }
        }

        private static void ScanPortableFonts()
        {
            lock (PortableFontsLock)
            {
                if (_portableFonts != null) return;
                Dictionary<string, string> fonts = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
                SortedSet<string> familyNames = new SortedSet<string>(StringComparer.OrdinalIgnoreCase);
                EnumerationOptions options = new EnumerationOptions
                {
                    RecurseSubdirectories = true,
                    IgnoreInaccessible = true,
                    MatchCasing = MatchCasing.CaseInsensitive
                };
                foreach (string folder in GetFontFolders())
                {
                    if (!Directory.Exists(folder)) continue;
                    foreach (string extension in FileExtensions)
                    {
                        foreach (string path in Directory.EnumerateFiles(folder, "*" + extension, options))
                        {
                            string family;
                            string style;
                            if (!ReadFontNames(path, out family, out style)) continue;
                            string formatName = extension == ".otf" ? " (OpenType)" : " (TrueType)";
                            string styleName = string.Equals(style, "Regular", StringComparison.OrdinalIgnoreCase)
                                ? "" : " " + style;
                            string name = family + styleName + formatName;
                            if (!fonts.ContainsKey(name)) fonts.Add(name, path);
                            familyNames.Add(family);
                        }
                    }
                }
                _portableFamilyNames = new List<string>(familyNames);
                _portableFonts = fonts;
            }
        }

        // The family (name id 1) and the style (name id 2) of a font, the names the Windows registry is keyed by
        private static bool ReadFontNames(string path, out string family, out string style)
        {
            family = null;
            style = null;
            try
            {
                using (BinaryReader reader = new BinaryReader(File.OpenRead(path)))
                {
                    reader.BaseStream.Position = 4;
                    int tableCount = ReadUInt16(reader);
                    long nameOffset = -1;
                    for (int i = 0; i < tableCount; i++)
                    {
                        reader.BaseStream.Position = 12 + 16 * i;
                        string tag = Encoding.ASCII.GetString(reader.ReadBytes(4));
                        reader.BaseStream.Position += 4;
                        long offset = ReadUInt32(reader);
                        if (tag == "name") nameOffset = offset;
                    }
                    if (nameOffset < 0) return false;
                    family = ReadName(reader, nameOffset, 1);
                    style = ReadName(reader, nameOffset, 2);
                }
            }
            catch (Exception)
            {
                return false;
            }
            if (string.IsNullOrWhiteSpace(family)) return false;
            family = family.Trim();
            style = string.IsNullOrWhiteSpace(style) ? "Regular" : style.Trim();
            return true;
        }

        // Windows English names first, then any Windows or Unicode name, then a Macintosh Roman name
        private static string ReadName(BinaryReader reader, long nameOffset, int nameId)
        {
            reader.BaseStream.Position = nameOffset + 2;
            int count = ReadUInt16(reader);
            long storage = nameOffset + ReadUInt16(reader);
            string best = null;
            int bestRank = int.MaxValue;
            for (int i = 0; i < count; i++)
            {
                reader.BaseStream.Position = nameOffset + 6 + 12 * i;
                int platformId = ReadUInt16(reader);
                int encodingId = ReadUInt16(reader);
                int languageId = ReadUInt16(reader);
                int id = ReadUInt16(reader);
                int length = ReadUInt16(reader);
                int offset = ReadUInt16(reader);
                if (id != nameId) continue;
                int rank;
                if (platformId == 3 && languageId == 0x409) rank = 0;
                else if (platformId == 3 || platformId == 0) rank = 1;
                else if (platformId == 1 && encodingId == 0) rank = 2;
                else continue;
                if (rank >= bestRank) continue;
                long position = reader.BaseStream.Position;
                reader.BaseStream.Position = storage + offset;
                byte[] bytes = reader.ReadBytes(length);
                reader.BaseStream.Position = position;
                best = rank == 2 ? Encoding.Latin1.GetString(bytes) : Encoding.BigEndianUnicode.GetString(bytes);
                bestRank = rank;
            }
            return best;
        }
    }
}
