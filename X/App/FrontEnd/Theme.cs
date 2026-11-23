// The appearance of the front end (D069, a maintainer exception to D061): Light, the WinForms look of the original
// and the default, or Dark, warm greys in the manner of the Claude apps. The original has no themes: its forms carry
// system colours and some fixed ones (white backgrounds, black text), which the dark appearance maps here, at the
// drawing, so no original file changes. Data colours (part colours, curves, swatches) keep their values. The choice is
// PrePoMax-X's own setting (appearance.json in the PrePoMax-X folder of the user's settings, or PREPOMAXX_THEME), not
// the original's settings, so settings and PMX files stay those of Windows PrePoMax. The toggle (AppearanceToggle)
// switches the running application.
using System;
using System.IO;
using System.Text.Json;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;
using Avalonia.Platform;

namespace PrePoMaxX.FrontEnd
{
    internal enum Appearance { Light, Dark, System }

    internal static class UiTheme
    {
        public static Appearance Setting { get; private set; } = Appearance.Light;
        public static bool Dark { get; private set; }

        // Palette ---------------------------------------------------------------------------------------------------------
        public static Color Window, Control, ButtonFace, ButtonBorder, Frame, LightFrame, Text, GrayText, Highlight,
            HighlightText, HoverFace, CheckedFace, CheckedBorder, HeaderFace, HeaderCurrent, GridLine, ReadOnlyText, Info,
            Error, Warning, Link;

        static void Palette()
        {
            if (Dark)
            {
                Window = Rgb(0x1F, 0x1E, 0x1D); Control = Rgb(0x26, 0x26, 0x24); ButtonFace = Rgb(0x35, 0x34, 0x31);
                ButtonBorder = Rgb(0x52, 0x51, 0x4C); Frame = Rgb(0x6B, 0x6A, 0x64); LightFrame = Rgb(0x3A, 0x39, 0x35);
                Text = Rgb(0xEC, 0xEB, 0xE4); GrayText = Rgb(0x8F, 0x8D, 0x86); Highlight = Rgb(0xB8, 0x5A, 0x3B);
                HighlightText = Rgb(0xFF, 0xFF, 0xFF); HoverFace = Rgb(0x3B, 0x3A, 0x36); CheckedFace = Rgb(0x4A, 0x37, 0x2E);
                CheckedBorder = Rgb(0xD9, 0x77, 0x57); HeaderFace = Rgb(0x2E, 0x2D, 0x2A); HeaderCurrent = Rgb(0x4A, 0x37, 0x2E);
                GridLine = Rgb(0x36, 0x35, 0x31); ReadOnlyText = Rgb(0xB0, 0xAE, 0xA6); Info = Rgb(0x3A, 0x36, 0x2A);
                Error = Rgb(0xF2, 0x7A, 0x6E); Warning = Rgb(0xF0, 0xA8, 0x4A); Link = Rgb(0x7F, 0xB2, 0xF0);
            }
            else
            {
                Window = Colors.White; Control = Rgb(0xF0, 0xF0, 0xF0); ButtonFace = Rgb(0xE1, 0xE1, 0xE1);
                ButtonBorder = Rgb(0xAD, 0xAD, 0xAD); Frame = Rgb(0x7A, 0x7A, 0x7A); LightFrame = Rgb(0xDC, 0xDC, 0xDC);
                Text = Colors.Black; GrayText = Rgb(0x6D, 0x6D, 0x6D); Highlight = Rgb(0x00, 0x78, 0xD7);
                HighlightText = Colors.White; HoverFace = Rgb(0xE5, 0xF1, 0xFB); CheckedFace = Rgb(0xCC, 0xE8, 0xFF);
                CheckedBorder = Rgb(0x99, 0xD1, 0xFF); HeaderFace = Rgb(0xF7, 0xF7, 0xF7); HeaderCurrent = Rgb(0xD9, 0xEB, 0xF9);
                GridLine = Rgb(0xE6, 0xE6, 0xE6); ReadOnlyText = Rgb(80, 80, 80); Info = Rgb(0xFF, 0xFF, 0xE1);
                Error = Colors.Red; Warning = Colors.DarkOrange; Link = Rgb(0x00, 0x66, 0xCC);
            }
        }

        static Color Rgb(byte r, byte g, byte b) => Color.FromRgb(r, g, b);

        // Setting ---------------------------------------------------------------------------------------------------------
        /// <summary>The PrePoMax-X folder of the user's settings: ~/Library/Application Support (macOS),
        /// $XDG_CONFIG_HOME or ~/.config (Linux), %APPDATA% (Windows).</summary>
        static string SettingsFile()
        {
            string folder;
            if (OperatingSystem.IsMacOS())
                folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Library", "Application Support");
            else if (OperatingSystem.IsLinux())
                folder = Environment.GetEnvironmentVariable("XDG_CONFIG_HOME") is string xdg && xdg.Length > 0 ? xdg :
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".config");
            else
                folder = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            return Path.Combine(folder, "PrePoMax-X", "appearance.json");
        }

        static bool TryParse(string text, out Appearance value) =>
            Enum.TryParse(text?.Trim(), true, out value) && Enum.IsDefined(typeof(Appearance), value);

        /// <summary>Reads the setting (PREPOMAXX_THEME first) and resolves System from the platform's appearance; before
        /// anything is drawn.</summary>
        public static void Load(IPlatformSettings platform)
        {
            Appearance setting = Appearance.Light;
            try
            {
                string file = SettingsFile();
                if (File.Exists(file))
                    using (var document = JsonDocument.Parse(File.ReadAllText(file)))
                        if (document.RootElement.TryGetProperty("appearance", out JsonElement element) && TryParse(element.GetString(), out Appearance stored))
                            setting = stored;
            }
            catch (Exception error) { Console.Error.WriteLine("appearance.json not read: " + error.Message); }
            if (TryParse(Environment.GetEnvironmentVariable("PREPOMAXX_THEME"), out Appearance forced)) setting = forced;
            Setting = setting;
            Dark = setting == Appearance.Dark ||
                   setting == Appearance.System && platform?.GetColorValues().ThemeVariant == PlatformThemeVariant.Dark;
            Palette();
            Viewport();
        }

        /// <summary>Switches the running application (the toggle): the palette, Fluent's variant and the shared brushes
        /// change, every window is synchronized again and redrawn; the choice is saved for the next start.</summary>
        public static void Switch(bool dark)
        {
            Dark = dark;
            Palette();
            Viewport();
            var application = Application.Current;
            if (application != null)
            {
                application.RequestedThemeVariant = dark ? Avalonia.Styling.ThemeVariant.Dark : Avalonia.Styling.ThemeVariant.Light;
                Accent(application);
            }
            Look.Init();
            // A forced appearance (PREPOMAXX_THEME: probes, tests) leaves the user's setting as it is
            if (!TryParse(Environment.GetEnvironmentVariable("PREPOMAXX_THEME"), out _))
            try { Save(dark ? Appearance.Dark : Appearance.Light); }
            catch (Exception error) { Console.Error.WriteLine("appearance.json not written: " + error.Message); }
            Ui.Restyle();
        }

        /// <summary>The 3D view in the dark appearance: the background of the Graphics settings (white, solid or the
        /// gradient) drawn as warm light greys, not too dark for the black annotations and mesh edges, and not white;
        /// the settings keep their colours.</summary>
        static void Viewport() => vtkControl.Native.VtkNativeView.BackgroundFilter = Dark ? (Func<double[], double[]>)ViewportColor : null;

        static double[] ViewportColor(double[] rgb)
        {
            double l = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
            double t = 0.44 + 0.28 * l;   // white 0.72 (#B8B7B2), the default gradient's darker end about 0.62
            return new[] { t, t * 0.995, t * 0.968 };
        }

        /// <summary>Fluent's accent (focus borders, selected items) in the dark appearance; Fluent's own in the light one.</summary>
        public static void Accent(Application application)
        {
            foreach (string key in new[] { "SystemAccentColor", "SystemAccentColorDark1", "SystemAccentColorLight1" })
                if (Dark) application.Resources[key] = CheckedBorder; else application.Resources.Remove(key);
        }

        public static void Save(Appearance value)
        {
            string file = SettingsFile();
            Directory.CreateDirectory(Path.GetDirectoryName(file));
            File.WriteAllText(file, JsonSerializer.Serialize(new { appearance = value.ToString() }) + "\n");
            Setting = value;
        }

        // Colours of the original -------------------------------------------------------------------------------------------
        /// <summary>A system colour of the original in the current appearance.</summary>
        public static Color? SystemColor(System.Drawing.KnownColor color)
        {
            switch (color)
            {
                case System.Drawing.KnownColor.Control: case System.Drawing.KnownColor.ButtonFace: case System.Drawing.KnownColor.Menu:
                case System.Drawing.KnownColor.MenuBar: case System.Drawing.KnownColor.GradientInactiveCaption: return Control;
                case System.Drawing.KnownColor.Window: return Window;
                case System.Drawing.KnownColor.ControlLightLight: case System.Drawing.KnownColor.ButtonHighlight:
                    return Dark ? ButtonFace : Colors.White;
                case System.Drawing.KnownColor.HighlightText: return HighlightText;
                case System.Drawing.KnownColor.ControlText: case System.Drawing.KnownColor.WindowText: case System.Drawing.KnownColor.MenuText:
                case System.Drawing.KnownColor.InfoText: case System.Drawing.KnownColor.ActiveCaptionText: return Text;
                case System.Drawing.KnownColor.ControlDark: case System.Drawing.KnownColor.ButtonShadow:
                    return Dark ? ButtonBorder : Rgb(0xA0, 0xA0, 0xA0);
                case System.Drawing.KnownColor.ControlDarkDark: return Dark ? Frame : Rgb(0x69, 0x69, 0x69);
                case System.Drawing.KnownColor.ControlLight: return Dark ? LightFrame : Rgb(0xE3, 0xE3, 0xE3);
                case System.Drawing.KnownColor.Highlight: case System.Drawing.KnownColor.MenuHighlight: return Highlight;
                case System.Drawing.KnownColor.HotTrack: return Dark ? Link : Rgb(0x00, 0x66, 0xCC);
                case System.Drawing.KnownColor.GrayText: case System.Drawing.KnownColor.InactiveCaptionText: return GrayText;
                case System.Drawing.KnownColor.AppWorkspace: return Dark ? Window : Rgb(0xAB, 0xAB, 0xAB);
                case System.Drawing.KnownColor.Info: return Info;
                case System.Drawing.KnownColor.ActiveCaption: return Dark ? HeaderCurrent : Rgb(0x99, 0xB4, 0xD1);
                case System.Drawing.KnownColor.InactiveCaption: return Dark ? HeaderFace : Rgb(0xBF, 0xCD, 0xDB);
                case System.Drawing.KnownColor.InactiveBorder: return Dark ? LightFrame : Rgb(0xF4, 0xF7, 0xFC);
                case System.Drawing.KnownColor.ActiveBorder: return Dark ? ButtonBorder : Rgb(0xB4, 0xB4, 0xB4);
                case System.Drawing.KnownColor.ScrollBar: return Dark ? ButtonFace : Rgb(0xC8, 0xC8, 0xC8);
                case System.Drawing.KnownColor.WindowFrame: return Dark ? Frame : Rgb(0x64, 0x64, 0x64);
            }
            return null;
        }

        /// <summary>A fixed colour of the original used as a background or drawn shape: in the dark appearance greys and
        /// near-whites (white backgrounds, pale headers, the info yellow) turn dark, keeping their order and tint; colours
        /// with a hue keep their values (part colours, curves, swatches).</summary>
        public static Color Back(Color color)
        {
            if (!Dark || color.A == 0) return color;
            Hsl(color, out double h, out double s, out double l);
            if (s < 0.12 || l > 0.86 || l < 0.08) return Invert(color, h, s, l);
            return color;
        }

        /// <summary>A fixed colour of the original used for text or lines on a background: in the dark appearance black
        /// and greys turn light, dark colours (dark red, navy, the code editor's styles) are lightened to stay legible.</summary>
        public static Color Fore(Color color)
        {
            if (!Dark || color.A == 0) return color;
            Hsl(color, out double h, out double s, out double l);
            if (s < 0.12 || l < 0.08) return Invert(color, h, s, l);
            if (l < 0.62) return FromHsl(h, Math.Min(s, 0.85), 0.62 + 0.25 * l, color.A);
            return color;
        }

        /// <summary>Greys between the dark background (white) and the text colour (black); tinted pale colours keep their
        /// hue, darkened.</summary>
        static Color Invert(Color color, double h, double s, double l)
        {
            if (s < 0.12)
            {
                double t = 1 - l;   // 0 for white, 1 for black
                Color from = Window, to = Text;
                return Color.FromArgb(color.A, (byte)Math.Round(from.R + t * (to.R - from.R)), (byte)Math.Round(from.G + t * (to.G - from.G)),
                                      (byte)Math.Round(from.B + t * (to.B - from.B)));
            }
            return FromHsl(h, Math.Min(s, 0.35), 0.12 + (1 - l) * 0.8, color.A);
        }

        static void Hsl(Color c, out double h, out double s, out double l)
        {
            double r = c.R / 255.0, g = c.G / 255.0, b = c.B / 255.0;
            double max = Math.Max(r, Math.Max(g, b)), min = Math.Min(r, Math.Min(g, b));
            l = (max + min) / 2;
            if (max == min) { h = 0; s = 0; return; }
            double d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            h = max == r ? (g - b) / d + (g < b ? 6 : 0) : max == g ? (b - r) / d + 2 : (r - g) / d + 4;
            h /= 6;
        }

        static Color FromHsl(double h, double s, double l, byte a)
        {
            double q = l < 0.5 ? l * (1 + s) : l + s - l * s, p = 2 * l - q;
            double Channel(double t)
            {
                if (t < 0) t += 1; if (t > 1) t -= 1;
                return t < 1.0 / 6 ? p + (q - p) * 6 * t : t < 0.5 ? q : t < 2.0 / 3 ? p + (q - p) * (2.0 / 3 - t) * 6 : p;
            }
            return Color.FromArgb(a, (byte)Math.Round(255 * Channel(h + 1.0 / 3)), (byte)Math.Round(255 * Channel(h)),
                                  (byte)Math.Round(255 * Channel(h - 1.0 / 3)));
        }
    }

    /// <summary>The appearance toggle: one tool button at the right end of the main window's first tool strip row
    /// (the top ToolStripPanel), drawn by the front end, so no original form changes.</summary>
    internal sealed class AppearanceToggle : Button
    {
        protected override Type StyleKeyOverride => typeof(Button);

        public AppearanceToggle()
        {
            Classes.Add("tool");
            Focusable = false;
            HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Right;
            VerticalAlignment = Avalonia.Layout.VerticalAlignment.Top;
            Margin = new Thickness(0, 0, 4, 0);
            // A half-filled circle, the usual light/dark sign, in the text colour of the appearance
            var icon = new Canvas { Width = 16, Height = 16 };
            icon.Children.Add(new Avalonia.Controls.Shapes.Ellipse { Width = 13, Height = 13, StrokeThickness = 1.4, Stroke = Look.Text,
                                                                     [Canvas.LeftProperty] = 1.5, [Canvas.TopProperty] = 1.5 });
            icon.Children.Add(new Avalonia.Controls.Shapes.Path { Fill = Look.Text, Data = Geometry.Parse("M 8,2 A 6,6 0 0 1 8,14 Z") });
            Content = icon;
            Tip();
            Click += (s, e) => UiTheme.Switch(!UiTheme.Dark);
        }

        internal void Tip() => ToolTip.SetTip(this, UiTheme.Dark ? "Light appearance (PrePoMax-X)" : "Dark appearance (PrePoMax-X)");
    }
}
