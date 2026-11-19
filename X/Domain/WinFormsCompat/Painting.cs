// A recording GDI+ painting surface (M2). System.Drawing.Common is Windows-only on .NET 10, so the original
// paint handlers (the 3.0.1 layup diagram of FrmSection, the property grid's missing-value painter, original
// owner-drawn controls) draw on this Graphics instead: every call is kept as a command, in order, with the pen,
// brush, clip and smoothing state of the moment, and the UI replays the commands with its own painter (Qt's
// QPainter in X/UI). Same names and signatures as System.Drawing, so the original drawing code compiles unchanged.
using System.Collections.Generic;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Drawing.Text;

namespace System.Drawing
{
    /// <summary>One recorded drawing call: the GDI+ method name and its arguments (pens and brushes as copies).</summary>
    public sealed class PaintCommand
    {
        public PaintCommand(string name, object[] arguments) { Name = name; Arguments = arguments; }
        public string Name { get; }
        public object[] Arguments { get; }
        public override string ToString() => Name + "(" + string.Join(", ", Arguments) + ")";
    }

    public interface IDeviceContext : IDisposable { }

    public sealed class Graphics : IDeviceContext
    {
        readonly List<PaintCommand> commands = new List<PaintCommand>();
        readonly Stack<object[]> states = new Stack<object[]>();
        SmoothingMode smoothingMode = SmoothingMode.Default;
        TextRenderingHint textRenderingHint;
        RectangleF? clip;

        /// <summary>A surface of the given size in device pixels (the control's client area).</summary>
        public Graphics(Rectangle bounds) { VisibleClipBounds = bounds; }
        public static Func<string, object, SizeF> MeasureHandler;
        public IReadOnlyList<PaintCommand> Commands => commands;
        public RectangleF VisibleClipBounds { get; }
        public RectangleF ClipBounds => clip ?? VisibleClipBounds;
        public float DpiX => 96f;
        public float DpiY => 96f;
        public PageUnit PageUnit { get; set; } = PageUnit.Pixel;
        public CompositingQuality CompositingQuality { get; set; }
        public InterpolationMode InterpolationMode { get; set; }
        public PixelOffsetMode PixelOffsetMode { get; set; }
        public SmoothingMode SmoothingMode { get => smoothingMode; set { smoothingMode = value; Add("SmoothingMode", value); } }
        public TextRenderingHint TextRenderingHint { get => textRenderingHint; set { textRenderingHint = value; Add("TextRenderingHint", value); } }
        public Region Clip { get => new Region(ClipBounds); set => SetClip(value.Bounds); }

        void Add(string name, params object[] arguments) => commands.Add(new PaintCommand(name, arguments));
        static RectangleF F(Rectangle r) => new RectangleF(r.X, r.Y, r.Width, r.Height);
        static PointF[] F(Point[] points) { var result = new PointF[points.Length]; for (int i = 0; i < points.Length; i++) result[i] = points[i]; return result; }

        public void Clear(Color color) => Add("Clear", color);
        // Lines and shapes
        public void DrawLine(Pen pen, float x1, float y1, float x2, float y2) => Add("DrawLine", pen.Clone(), new PointF(x1, y1), new PointF(x2, y2));
        public void DrawLine(Pen pen, int x1, int y1, int x2, int y2) => DrawLine(pen, (float)x1, y1, x2, y2);
        public void DrawLine(Pen pen, Point a, Point b) => DrawLine(pen, a.X, a.Y, b.X, b.Y);
        public void DrawLine(Pen pen, PointF a, PointF b) => DrawLine(pen, a.X, a.Y, b.X, b.Y);
        public void DrawLines(Pen pen, PointF[] points) => Add("DrawLines", pen.Clone(), (PointF[])points.Clone());
        public void DrawLines(Pen pen, Point[] points) => DrawLines(pen, F(points));
        public void DrawRectangle(Pen pen, RectangleF r) => Add("DrawRectangle", pen.Clone(), r);
        public void DrawRectangle(Pen pen, Rectangle r) => DrawRectangle(pen, F(r));
        public void DrawRectangle(Pen pen, int x, int y, int width, int height) => DrawRectangle(pen, new RectangleF(x, y, width, height));
        public void DrawRectangle(Pen pen, float x, float y, float width, float height) => DrawRectangle(pen, new RectangleF(x, y, width, height));
        public void FillRectangle(Brush brush, RectangleF r) => Add("FillRectangle", brush.Clone(), r);
        public void FillRectangle(Brush brush, Rectangle r) => FillRectangle(brush, F(r));
        public void FillRectangle(Brush brush, int x, int y, int width, int height) => FillRectangle(brush, new RectangleF(x, y, width, height));
        public void FillRectangle(Brush brush, float x, float y, float width, float height) => FillRectangle(brush, new RectangleF(x, y, width, height));
        public void DrawEllipse(Pen pen, RectangleF r) => Add("DrawEllipse", pen.Clone(), r);
        public void DrawEllipse(Pen pen, Rectangle r) => DrawEllipse(pen, F(r));
        public void DrawEllipse(Pen pen, float x, float y, float width, float height) => DrawEllipse(pen, new RectangleF(x, y, width, height));
        public void FillEllipse(Brush brush, RectangleF r) => Add("FillEllipse", brush.Clone(), r);
        public void FillEllipse(Brush brush, Rectangle r) => FillEllipse(brush, F(r));
        public void FillEllipse(Brush brush, float x, float y, float width, float height) => FillEllipse(brush, new RectangleF(x, y, width, height));
        public void DrawPolygon(Pen pen, PointF[] points) => Add("DrawPolygon", pen.Clone(), (PointF[])points.Clone());
        public void DrawPolygon(Pen pen, Point[] points) => DrawPolygon(pen, F(points));
        public void FillPolygon(Brush brush, PointF[] points) => Add("FillPolygon", brush.Clone(), (PointF[])points.Clone());
        public void FillPolygon(Brush brush, Point[] points) => FillPolygon(brush, F(points));
        public void DrawPath(Pen pen, GraphicsPath path) => Add("DrawPath", pen.Clone(), path.Clone());
        public void FillPath(Brush brush, GraphicsPath path) => Add("FillPath", brush.Clone(), path.Clone());
        // Text
        public void DrawString(string text, Font font, Brush brush, PointF point) => Add("DrawString", text ?? "", font, brush.Clone(), new RectangleF(point, SizeF.Empty), null);
        public void DrawString(string text, Font font, Brush brush, float x, float y) => DrawString(text, font, brush, new PointF(x, y));
        public void DrawString(string text, Font font, Brush brush, RectangleF layout) => DrawString(text, font, brush, layout, null);
        public void DrawString(string text, Font font, Brush brush, RectangleF layout, StringFormat format) => Add("DrawString", text ?? "", font, brush.Clone(), layout, format);
        public void DrawString(string text, Font font, Brush brush, PointF point, StringFormat format) => Add("DrawString", text ?? "", font, brush.Clone(), new RectangleF(point, SizeF.Empty), format);
        /// <summary>TextRenderer.DrawText: text in a colour at a point or in a box with format flags.</summary>
        public void DrawText(string text, object font, RectangleF box, Color color, int flags) => Add("DrawText", text ?? "", font, box, color, flags);
        public SizeF MeasureString(string text, object font) => MeasureHandler != null ? MeasureHandler(text ?? "", font) : new SizeF((text ?? "").Length * 7f, 15f);
        public SizeF MeasureString(string text, object font, int width) => MeasureString(text, font);
        public SizeF MeasureString(string text, object font, SizeF layout, StringFormat format) => MeasureString(text, font);
        // Images
        public void DrawImage(Image image, Rectangle rectangle) => Add("DrawImage", image, F(rectangle));
        public void DrawImage(Image image, RectangleF rectangle) => Add("DrawImage", image, rectangle);
        public void DrawImage(Image image, int x, int y) => Add("DrawImage", image, new RectangleF(x, y, image?.Width ?? 0, image?.Height ?? 0));
        public void DrawImage(Image image, int x, int y, int width, int height) => Add("DrawImage", image, new RectangleF(x, y, width, height));
        public void DrawImage(Image image, Point point) => DrawImage(image, point.X, point.Y);
        // State
        public GraphicsState Save()
        {
            states.Push(new object[] { smoothingMode, textRenderingHint, clip });
            Add("Save");
            return new GraphicsState(states.Count);
        }
        public void Restore(GraphicsState state)
        {
            while (states.Count >= state.Depth && states.Count > 0)
            {
                object[] s = states.Pop();
                smoothingMode = (SmoothingMode)s[0]; textRenderingHint = (TextRenderingHint)s[1]; clip = (RectangleF?)s[2];
                Add("Restore");
            }
        }
        public void SetClip(RectangleF rectangle) { clip = rectangle; Add("SetClip", rectangle); }
        public void SetClip(Rectangle rectangle) => SetClip(F(rectangle));
        public void SetClip(RectangleF rectangle, CombineMode mode)
        {
            if (mode == CombineMode.Intersect && clip.HasValue) rectangle = RectangleF.Intersect(clip.Value, rectangle);
            SetClip(rectangle);
        }
        public void SetClip(Rectangle rectangle, CombineMode mode) => SetClip(F(rectangle), mode);
        public void IntersectClip(Rectangle rectangle) => SetClip(F(rectangle), CombineMode.Intersect);
        public void IntersectClip(RectangleF rectangle) => SetClip(rectangle, CombineMode.Intersect);
        public void ResetClip() { clip = null; Add("ResetClip"); }
        public void TranslateTransform(float dx, float dy) => Add("TranslateTransform", dx, dy);
        public void RotateTransform(float angle) => Add("RotateTransform", angle);
        public void ScaleTransform(float sx, float sy) => Add("ScaleTransform", sx, sy);
        public void ResetTransform() => Add("ResetTransform");
        public void Flush() { }
        public void Dispose() { }
    }

    public abstract class Brush : ICloneable, IDisposable
    {
        public abstract object Clone();
        public void Dispose() { }
    }
    public sealed class SolidBrush : Brush
    {
        public SolidBrush(Color color) { Color = color; }
        public Color Color { get; set; }
        public override object Clone() => new SolidBrush(Color);
        public override string ToString() => "SolidBrush " + Color;
    }
    public sealed class Pen : ICloneable, IDisposable
    {
        public Pen(Color color) : this(color, 1f) { }
        public Pen(Color color, float width) { Color = color; Width = width; }
        public Pen(Brush brush) : this(brush is SolidBrush s ? s.Color : Color.Black, 1f) { }
        public Pen(Brush brush, float width) : this(brush is SolidBrush s ? s.Color : Color.Black, width) { }
        public Color Color { get; set; }
        public float Width { get; set; }
        public DashStyle DashStyle { get; set; }
        public float[] DashPattern { get; set; }
        public LineCap StartCap { get; set; }
        public LineCap EndCap { get; set; }
        public CustomLineCap CustomStartCap { get; set; }
        public CustomLineCap CustomEndCap { get; set; }
        public LineJoin LineJoin { get; set; }
        public PenAlignment Alignment { get; set; }
        public object Clone() => MemberwiseClone();
        public void Dispose() { }
        public override string ToString() => "Pen " + Color + " " + Width + (DashStyle != DashStyle.Solid ? " " + DashStyle : "");
    }
    public static class Brushes
    {
        public static Brush Black => new SolidBrush(Color.Black);
        public static Brush White => new SolidBrush(Color.White);
        public static Brush Gray => new SolidBrush(Color.Gray);
        public static Brush Red => new SolidBrush(Color.Red);
        public static Brush Transparent => new SolidBrush(Color.Transparent);
    }
    public static class Pens
    {
        public static Pen Black => new Pen(Color.Black);
        public static Pen White => new Pen(Color.White);
        public static Pen Gray => new Pen(Color.Gray);
        public static Pen Red => new Pen(Color.Red);
    }
    public static class SystemBrushes
    {
        public static Brush Window => new SolidBrush(SystemColors.Window);
        public static Brush WindowText => new SolidBrush(SystemColors.WindowText);
        public static Brush Highlight => new SolidBrush(SystemColors.Highlight);
        public static Brush HighlightText => new SolidBrush(SystemColors.HighlightText);
        public static Brush Control => new SolidBrush(SystemColors.Control);
        public static Brush ControlText => new SolidBrush(SystemColors.ControlText);
        public static Brush GrayText => new SolidBrush(SystemColors.GrayText);
    }
    public static class SystemPens
    {
        public static Pen Control => new Pen(SystemColors.Control);
        public static Pen ControlDark => new Pen(SystemColors.ControlDark);
        public static Pen ControlDarkDark => new Pen(SystemColors.ControlDarkDark);
        public static Pen ControlLight => new Pen(SystemColors.ControlLight);
        public static Pen ControlText => new Pen(SystemColors.ControlText);
        public static Pen GrayText => new Pen(SystemColors.GrayText);
        public static Pen WindowText => new Pen(SystemColors.WindowText);
        public static Pen WindowFrame => new Pen(SystemColors.WindowFrame);
        public static Pen Highlight => new Pen(SystemColors.Highlight);
    }
    public enum PageUnit { World, Display, Pixel, Point, Inch, Document, Millimeter }
    public enum FontStyle { Regular = 0, Bold = 1, Italic = 2, Underline = 4, Strikeout = 8 }
    public enum GraphicsUnit { World, Display, Pixel, Point, Inch, Document, Millimeter }
    /// <summary>A font description (GDI+ fonts need GDI+): family, size in points and style.</summary>
    public class Font : IDisposable, ICloneable
    {
        public Font(string familyName, float emSize) : this(familyName, emSize, FontStyle.Regular) { }
        public Font(string familyName, float emSize, FontStyle style) { Name = familyName; Size = emSize; Style = style; }
        public Font(string familyName, float emSize, FontStyle style, GraphicsUnit unit) : this(familyName, emSize, style) { }
        public Font(string familyName, float emSize, FontStyle style, GraphicsUnit unit, byte gdiCharSet) : this(familyName, emSize, style) { }
        public Font(Font prototype, FontStyle style) : this(prototype.Name, prototype.Size, style) { }
        public string Name { get; }
        public float Size { get; }
        public float SizeInPoints => Size;
        public FontStyle Style { get; }
        public bool Bold => (Style & FontStyle.Bold) != 0;
        public bool Italic => (Style & FontStyle.Italic) != 0;
        public bool Underline => (Style & FontStyle.Underline) != 0;
        public int Height => (int)Math.Ceiling(Size * 96f / 72f * 1.2f);
        public FontFamily FontFamily => new FontFamily(Name);
        public object Clone() => MemberwiseClone();
        public void Dispose() { }
        public override string ToString() => Name + " " + Size + "pt " + Style;
    }
    public sealed class FontFamily
    {
        public FontFamily(string name) { Name = name; }
        public string Name { get; }
        public static FontFamily GenericSansSerif => new FontFamily("Microsoft Sans Serif");
        public static FontFamily GenericMonospace => new FontFamily("Courier New");
    }
    /// <summary>An image by reference: the original file, or encoded bytes, with its pixel size.</summary>
    public abstract class Image : IDisposable, ICloneable
    {
        public int Width { get; protected set; }
        public int Height { get; protected set; }
        public Size Size => new Size(Width, Height);
        public object Tag { get; set; }
        public abstract object Clone();
        public void Dispose() { }
    }
    /// <summary>A window icon (the renderer shows the application's icon).</summary>
    public sealed class Icon : IDisposable, ICloneable
    {
        public int Width { get; set; } = 32;
        public int Height { get; set; } = 32;
        public Size Size => new Size(Width, Height);
        public object Clone() => MemberwiseClone();
        public void Dispose() { }
    }
    public enum ContentAlignment
    {
        TopLeft = 1, TopCenter = 2, TopRight = 4, MiddleLeft = 16, MiddleCenter = 32, MiddleRight = 64,
        BottomLeft = 256, BottomCenter = 512, BottomRight = 1024,
    }
    public sealed class Region : IDisposable
    {
        public Region() { Bounds = RectangleF.Empty; }
        public Region(RectangleF rectangle) { Bounds = rectangle; }
        public Region(Rectangle rectangle) { Bounds = new RectangleF(rectangle.X, rectangle.Y, rectangle.Width, rectangle.Height); }
        public RectangleF Bounds { get; }
        public RectangleF GetBounds(Graphics graphics) => Bounds;
        public void Dispose() { }
    }
    public sealed class StringFormat : IDisposable, ICloneable
    {
        public StringFormat() { }
        public StringFormat(StringFormatFlags flags) { FormatFlags = flags; }
        public StringAlignment Alignment { get; set; }
        public StringAlignment LineAlignment { get; set; }
        public StringFormatFlags FormatFlags { get; set; }
        public StringTrimming Trimming { get; set; }
        public static StringFormat GenericDefault => new StringFormat();
        public static StringFormat GenericTypographic => new StringFormat();
        public object Clone() => MemberwiseClone();
        public void Dispose() { }
    }
    public enum StringAlignment { Near, Center, Far }
    [Flags] public enum StringFormatFlags { DirectionRightToLeft = 1, DirectionVertical = 2, FitBlackBox = 4, DisplayFormatControl = 32, NoFontFallback = 1024, MeasureTrailingSpaces = 2048, NoWrap = 4096, LineLimit = 8192, NoClip = 16384 }
    public enum StringTrimming { None, Character, Word, EllipsisCharacter, EllipsisWord, EllipsisPath }
}

namespace System.Drawing.Drawing2D
{
    public enum SmoothingMode { Invalid = -1, Default = 0, HighSpeed = 1, HighQuality = 2, None = 3, AntiAlias = 4 }
    public enum DashStyle { Solid, Dash, Dot, DashDot, DashDotDot, Custom }
    public enum LineCap { Flat = 0, Square = 1, Round = 2, Triangle = 3, NoAnchor = 16, SquareAnchor = 17, RoundAnchor = 18, DiamondAnchor = 19, ArrowAnchor = 20, Custom = 255 }
    public enum LineJoin { Miter, Bevel, Round, MiterClipped }
    public enum PenAlignment { Center, Inset, Outset, Left, Right }
    public enum CombineMode { Replace, Intersect, Union, Xor, Exclude, Complement }
    public enum CompositingQuality { Invalid = -1, Default, HighSpeed, HighQuality, GammaCorrected, AssumeLinear }
    public enum InterpolationMode { Invalid = -1, Default, Low, High, Bilinear, Bicubic, NearestNeighbor, HighQualityBilinear, HighQualityBicubic }
    public enum PixelOffsetMode { Invalid = -1, Default, HighSpeed, HighQuality, None, Half }
    public enum HatchStyle { Horizontal, Vertical, ForwardDiagonal, BackwardDiagonal, Cross, DiagonalCross }
    public sealed class GraphicsState { internal GraphicsState(int depth) { Depth = depth; } internal int Depth { get; } }
    public class CustomLineCap : ICloneable, IDisposable { public object Clone() => MemberwiseClone(); public void Dispose() { } }
    /// <summary>An arrow head of the given width and height (in pen widths), filled unless told otherwise.</summary>
    public sealed class AdjustableArrowCap : CustomLineCap
    {
        public AdjustableArrowCap(float width, float height) : this(width, height, true) { }
        public AdjustableArrowCap(float width, float height, bool isFilled) { Width = width; Height = height; Filled = isFilled; }
        public float Width { get; set; }
        public float Height { get; set; }
        public bool Filled { get; set; }
    }
    /// <summary>A path as its figures of points (lines, rectangles, arcs flattened by the replay).</summary>
    public sealed class GraphicsPath : ICloneable, IDisposable
    {
        readonly List<PaintCommand> parts = new List<PaintCommand>();
        public IReadOnlyList<PaintCommand> Parts => parts;
        public void AddLine(float x1, float y1, float x2, float y2) => parts.Add(new PaintCommand("Line", new object[] { new PointF(x1, y1), new PointF(x2, y2) }));
        public void AddLine(PointF a, PointF b) => AddLine(a.X, a.Y, b.X, b.Y);
        public void AddLine(int x1, int y1, int x2, int y2) => AddLine((float)x1, y1, x2, y2);
        public void AddLines(PointF[] points) => parts.Add(new PaintCommand("Lines", new object[] { (PointF[])points.Clone() }));
        public void AddRectangle(RectangleF r) => parts.Add(new PaintCommand("Rectangle", new object[] { r }));
        public void AddRectangle(Rectangle r) => AddRectangle(new RectangleF(r.X, r.Y, r.Width, r.Height));
        public void AddEllipse(RectangleF r) => parts.Add(new PaintCommand("Ellipse", new object[] { r }));
        public void AddArc(RectangleF r, float startAngle, float sweepAngle) => parts.Add(new PaintCommand("Arc", new object[] { r, startAngle, sweepAngle }));
        public void AddArc(Rectangle r, float startAngle, float sweepAngle) => AddArc(new RectangleF(r.X, r.Y, r.Width, r.Height), startAngle, sweepAngle);
        public void AddArc(float x, float y, float width, float height, float startAngle, float sweepAngle) => AddArc(new RectangleF(x, y, width, height), startAngle, sweepAngle);
        public void AddPolygon(PointF[] points) => parts.Add(new PaintCommand("Polygon", new object[] { (PointF[])points.Clone() }));
        public void CloseFigure() => parts.Add(new PaintCommand("Close", new object[0]));
        public void CloseAllFigures() => CloseFigure();
        public void StartFigure() => parts.Add(new PaintCommand("Start", new object[0]));
        public object Clone() { var copy = new GraphicsPath(); copy.parts.AddRange(parts); return copy; }
        public void Dispose() { }
    }
}

namespace System.Drawing.Text
{
    public enum TextRenderingHint { SystemDefault, SingleBitPerPixelGridFit, SingleBitPerPixel, AntiAliasGridFit, AntiAlias, ClearTypeGridFit }
}

namespace System.Drawing.Imaging
{
    public sealed class ImageFormat
    {
        ImageFormat(string name) { Name = name; }
        public string Name { get; }
        public static ImageFormat Png { get; } = new ImageFormat("Png");
        public static ImageFormat Bmp { get; } = new ImageFormat("Bmp");
        public static ImageFormat Jpeg { get; } = new ImageFormat("Jpeg");
        public static ImageFormat Gif { get; } = new ImageFormat("Gif");
        public override string ToString() => Name;
    }
}
