// A compact light theme close to the WinForms look the original forms are designed for: Segoe UI 9 pt at 96 DPI is
// 12 px text in 23 px buttons, 20 px text boxes and 21 px combo boxes; Fluent's touch-friendly minimum sizes would
// not fit the designer bounds, so they are removed and the paddings narrowed.
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Presenters;
using Avalonia.Controls.Primitives;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Styling;

namespace PrePoMaxX.FrontEnd
{
    internal static class Look
    {
        public const double FontSize = 12;
        public static readonly IBrush Control = new SolidColorBrush(Color.FromRgb(0xF0, 0xF0, 0xF0));
        public static readonly IBrush Window = Brushes.White;
        public static readonly IBrush ButtonFace = new SolidColorBrush(Color.FromRgb(0xE1, 0xE1, 0xE1));
        public static readonly IBrush ButtonBorder = new SolidColorBrush(Color.FromRgb(0xAD, 0xAD, 0xAD));
        public static readonly IBrush Frame = new SolidColorBrush(Color.FromRgb(0x7A, 0x7A, 0x7A));
        public static readonly IBrush LightFrame = new SolidColorBrush(Color.FromRgb(0xDC, 0xDC, 0xDC));
        public static readonly IBrush Highlight = new SolidColorBrush(Color.FromRgb(0x00, 0x78, 0xD7));
        public static readonly IBrush HoverFace = new SolidColorBrush(Color.FromRgb(0xE5, 0xF1, 0xFB));
        public static readonly IBrush CheckedFace = new SolidColorBrush(Color.FromRgb(0xCC, 0xE8, 0xFF));
        public static readonly IBrush CheckedBorder = new SolidColorBrush(Color.FromRgb(0x99, 0xD1, 0xFF));
        public static readonly IBrush GrayText = new SolidColorBrush(Color.FromRgb(0x6D, 0x6D, 0x6D));
        public static readonly Typeface Typeface = new Typeface(FontFamily.Default);
        /// <summary>Linux: the default family when one with Segoe UI's widths is installed (the forms' designer bounds
        /// are made for it; Liberation Sans and Arimo have Arial's metrics, close to Segoe UI, where DejaVu Sans, the
        /// usual default, is wider). macOS keeps its system font, which fits the bounds.</summary>
        public static string LayoutFamily()
        {
            if (!System.OperatingSystem.IsLinux()) return null;
            var installed = new System.Collections.Generic.HashSet<string>(SkiaSharp.SKFontManager.Default.GetFontFamilies());
            foreach (string family in new[] { "Segoe UI", "Liberation Sans", "Arimo" })
                if (installed.Contains(family)) return family;
            return null;
        }
        public static readonly FontFamily Monospace = new FontFamily("Menlo, Consolas, DejaVu Sans Mono, monospace");

        static Style S<T>(System.Func<Selector, Selector> selector, params (AvaloniaProperty, object)[] setters)
        {
            var style = new Style(selector);
            foreach (var (property, value) in setters) style.Setters.Add(new Setter(property, value));
            return style;
        }

        public static void Add(Styles styles)
        {
            var thin = new Thickness(1);
            styles.Add(S<TemplatedControl>(x => x.Is<TemplatedControl>(), (TemplatedControl.FontSizeProperty, FontSize)));
            styles.Add(S<TextBlock>(x => x.OfType<TextBlock>(), (TextBlock.FontSizeProperty, FontSize)));
            styles.Add(S<Button>(x => x.OfType<Button>(), (Layoutable.MinHeightProperty, 0.0), (Layoutable.MinWidthProperty, 0.0),
                (TemplatedControl.PaddingProperty, new Thickness(4, 1)), (TemplatedControl.CornerRadiusProperty, new CornerRadius(2)),
                (TemplatedControl.BackgroundProperty, ButtonFace), (TemplatedControl.BorderBrushProperty, ButtonBorder),
                (TemplatedControl.BorderThicknessProperty, thin), (ContentControl.HorizontalContentAlignmentProperty, HorizontalAlignment.Center),
                (ContentControl.VerticalContentAlignmentProperty, VerticalAlignment.Center)));
            styles.Add(S<ToggleButton>(x => x.OfType<ToggleButton>(), (Layoutable.MinHeightProperty, 0.0), (Layoutable.MinWidthProperty, 0.0),
                (TemplatedControl.PaddingProperty, new Thickness(3, 1)), (TemplatedControl.CornerRadiusProperty, new CornerRadius(2))));
            styles.Add(S<TextBox>(x => x.OfType<TextBox>(), (Layoutable.MinHeightProperty, 0.0), (Layoutable.MinWidthProperty, 0.0),
                (TemplatedControl.PaddingProperty, new Thickness(3, 1)), (TemplatedControl.CornerRadiusProperty, new CornerRadius(0)),
                (TemplatedControl.BorderThicknessProperty, thin), (TextBox.VerticalContentAlignmentProperty, VerticalAlignment.Center),
                (TemplatedControl.BackgroundProperty, Window), (TemplatedControl.BorderBrushProperty, ButtonBorder)));
            styles.Add(S<TextBox>(x => x.OfType<TextBox>().Class(":readonly"), (TemplatedControl.BackgroundProperty, Control)));
            styles.Add(S<ComboBox>(x => x.OfType<ComboBox>(), (Layoutable.MinHeightProperty, 0.0), (Layoutable.MinWidthProperty, 0.0),
                (TemplatedControl.PaddingProperty, new Thickness(4, 0, 0, 0)), (TemplatedControl.CornerRadiusProperty, new CornerRadius(0)),
                (TemplatedControl.BorderThicknessProperty, thin), (ComboBox.VerticalContentAlignmentProperty, VerticalAlignment.Center)));
            styles.Add(S<NumericUpDown>(x => x.OfType<NumericUpDown>(), (Layoutable.MinHeightProperty, 0.0), (Layoutable.MinWidthProperty, 0.0),
                (TemplatedControl.PaddingProperty, new Thickness(2, 0)), (TemplatedControl.CornerRadiusProperty, new CornerRadius(0))));
            styles.Add(S<CheckBox>(x => x.OfType<CheckBox>(), (Layoutable.MinHeightProperty, 0.0), (Layoutable.MinWidthProperty, 0.0),
                (TemplatedControl.PaddingProperty, new Thickness(4, 0, 0, 0)), (ContentControl.VerticalContentAlignmentProperty, VerticalAlignment.Center)));
            styles.Add(S<RadioButton>(x => x.OfType<RadioButton>(), (Layoutable.MinHeightProperty, 0.0), (Layoutable.MinWidthProperty, 0.0),
                (TemplatedControl.PaddingProperty, new Thickness(4, 0, 0, 0)), (ContentControl.VerticalContentAlignmentProperty, VerticalAlignment.Center)));
            styles.Add(S<MenuItem>(x => x.OfType<MenuItem>(), (TemplatedControl.FontSizeProperty, FontSize)));
            styles.Add(S<Menu>(x => x.OfType<Menu>(), (Layoutable.MinHeightProperty, 0.0), (TemplatedControl.BackgroundProperty, Window)));
            styles.Add(S<ProgressBar>(x => x.OfType<ProgressBar>(), (Layoutable.MinHeightProperty, 0.0), (Layoutable.MinWidthProperty, 0.0)));
            styles.Add(S<Slider>(x => x.OfType<Slider>(), (Layoutable.MinHeightProperty, 0.0), (Layoutable.MinWidthProperty, 0.0)));
            styles.Add(S<ScrollBar>(x => x.OfType<ScrollBar>(), (ScrollBar.AllowAutoHideProperty, false)));
            // Tool strip buttons: flat, the hovered and checked faces of the WinForms professional renderer
            styles.Add(S<Button>(x => x.OfType<Button>().Class("tool"), (TemplatedControl.BackgroundProperty, Brushes.Transparent),
                (TemplatedControl.BorderBrushProperty, Brushes.Transparent), (TemplatedControl.PaddingProperty, new Thickness(3)),
                (TemplatedControl.CornerRadiusProperty, new CornerRadius(0))));
            styles.Add(S<ToggleButton>(x => x.OfType<ToggleButton>().Class("tool"), (TemplatedControl.BackgroundProperty, Brushes.Transparent),
                (TemplatedControl.BorderBrushProperty, Brushes.Transparent), (TemplatedControl.BorderThicknessProperty, thin),
                (TemplatedControl.PaddingProperty, new Thickness(2)), (TemplatedControl.CornerRadiusProperty, new CornerRadius(0))));
            styles.Add(S<ToggleButton>(x => x.OfType<ToggleButton>().Class("tool").Class(":checked").Template().OfType<ContentPresenter>().Name("PART_ContentPresenter"),
                (ContentPresenter.BackgroundProperty, CheckedFace), (ContentPresenter.BorderBrushProperty, CheckedBorder)));
            styles.Add(S<ToggleButton>(x => x.OfType<ToggleButton>().Class("tool").Class(":pointerover").Template().OfType<ContentPresenter>().Name("PART_ContentPresenter"),
                (ContentPresenter.BackgroundProperty, HoverFace), (ContentPresenter.BorderBrushProperty, CheckedBorder)));
            styles.Add(S<Button>(x => x.OfType<Button>().Class("tool").Class(":pointerover").Template().OfType<ContentPresenter>().Name("PART_ContentPresenter"),
                (ContentPresenter.BackgroundProperty, HoverFace), (ContentPresenter.BorderBrushProperty, CheckedBorder)));
        }
    }
}
