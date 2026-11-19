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
        /// <summary>Drawing on a bitmap: the commands are kept with it (Bitmap.Drawing) for the renderer.</summary>
        public static Graphics FromImage(Image image)
        {
            var graphics = new Graphics(new Rectangle(0, 0, image.Width, image.Height));
            if (image is Bitmap bitmap) bitmap.Drawing = graphics;
            return graphics;
        }
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
    // Every named colour of System.Drawing.Color, as GDI+ has (a new recording object each time)
    public static class Brushes
    {
        public static Brush Transparent => new SolidBrush(Color.Transparent);
        public static Brush AliceBlue => new SolidBrush(Color.AliceBlue);
        public static Brush AntiqueWhite => new SolidBrush(Color.AntiqueWhite);
        public static Brush Aqua => new SolidBrush(Color.Aqua);
        public static Brush Aquamarine => new SolidBrush(Color.Aquamarine);
        public static Brush Azure => new SolidBrush(Color.Azure);
        public static Brush Beige => new SolidBrush(Color.Beige);
        public static Brush Bisque => new SolidBrush(Color.Bisque);
        public static Brush Black => new SolidBrush(Color.Black);
        public static Brush BlanchedAlmond => new SolidBrush(Color.BlanchedAlmond);
        public static Brush Blue => new SolidBrush(Color.Blue);
        public static Brush BlueViolet => new SolidBrush(Color.BlueViolet);
        public static Brush Brown => new SolidBrush(Color.Brown);
        public static Brush BurlyWood => new SolidBrush(Color.BurlyWood);
        public static Brush CadetBlue => new SolidBrush(Color.CadetBlue);
        public static Brush Chartreuse => new SolidBrush(Color.Chartreuse);
        public static Brush Chocolate => new SolidBrush(Color.Chocolate);
        public static Brush Coral => new SolidBrush(Color.Coral);
        public static Brush CornflowerBlue => new SolidBrush(Color.CornflowerBlue);
        public static Brush Cornsilk => new SolidBrush(Color.Cornsilk);
        public static Brush Crimson => new SolidBrush(Color.Crimson);
        public static Brush Cyan => new SolidBrush(Color.Cyan);
        public static Brush DarkBlue => new SolidBrush(Color.DarkBlue);
        public static Brush DarkCyan => new SolidBrush(Color.DarkCyan);
        public static Brush DarkGoldenrod => new SolidBrush(Color.DarkGoldenrod);
        public static Brush DarkGray => new SolidBrush(Color.DarkGray);
        public static Brush DarkGreen => new SolidBrush(Color.DarkGreen);
        public static Brush DarkKhaki => new SolidBrush(Color.DarkKhaki);
        public static Brush DarkMagenta => new SolidBrush(Color.DarkMagenta);
        public static Brush DarkOliveGreen => new SolidBrush(Color.DarkOliveGreen);
        public static Brush DarkOrange => new SolidBrush(Color.DarkOrange);
        public static Brush DarkOrchid => new SolidBrush(Color.DarkOrchid);
        public static Brush DarkRed => new SolidBrush(Color.DarkRed);
        public static Brush DarkSalmon => new SolidBrush(Color.DarkSalmon);
        public static Brush DarkSeaGreen => new SolidBrush(Color.DarkSeaGreen);
        public static Brush DarkSlateBlue => new SolidBrush(Color.DarkSlateBlue);
        public static Brush DarkSlateGray => new SolidBrush(Color.DarkSlateGray);
        public static Brush DarkTurquoise => new SolidBrush(Color.DarkTurquoise);
        public static Brush DarkViolet => new SolidBrush(Color.DarkViolet);
        public static Brush DeepPink => new SolidBrush(Color.DeepPink);
        public static Brush DeepSkyBlue => new SolidBrush(Color.DeepSkyBlue);
        public static Brush DimGray => new SolidBrush(Color.DimGray);
        public static Brush DodgerBlue => new SolidBrush(Color.DodgerBlue);
        public static Brush Firebrick => new SolidBrush(Color.Firebrick);
        public static Brush FloralWhite => new SolidBrush(Color.FloralWhite);
        public static Brush ForestGreen => new SolidBrush(Color.ForestGreen);
        public static Brush Fuchsia => new SolidBrush(Color.Fuchsia);
        public static Brush Gainsboro => new SolidBrush(Color.Gainsboro);
        public static Brush GhostWhite => new SolidBrush(Color.GhostWhite);
        public static Brush Gold => new SolidBrush(Color.Gold);
        public static Brush Goldenrod => new SolidBrush(Color.Goldenrod);
        public static Brush Gray => new SolidBrush(Color.Gray);
        public static Brush Green => new SolidBrush(Color.Green);
        public static Brush GreenYellow => new SolidBrush(Color.GreenYellow);
        public static Brush Honeydew => new SolidBrush(Color.Honeydew);
        public static Brush HotPink => new SolidBrush(Color.HotPink);
        public static Brush IndianRed => new SolidBrush(Color.IndianRed);
        public static Brush Indigo => new SolidBrush(Color.Indigo);
        public static Brush Ivory => new SolidBrush(Color.Ivory);
        public static Brush Khaki => new SolidBrush(Color.Khaki);
        public static Brush Lavender => new SolidBrush(Color.Lavender);
        public static Brush LavenderBlush => new SolidBrush(Color.LavenderBlush);
        public static Brush LawnGreen => new SolidBrush(Color.LawnGreen);
        public static Brush LemonChiffon => new SolidBrush(Color.LemonChiffon);
        public static Brush LightBlue => new SolidBrush(Color.LightBlue);
        public static Brush LightCoral => new SolidBrush(Color.LightCoral);
        public static Brush LightCyan => new SolidBrush(Color.LightCyan);
        public static Brush LightGoldenrodYellow => new SolidBrush(Color.LightGoldenrodYellow);
        public static Brush LightGreen => new SolidBrush(Color.LightGreen);
        public static Brush LightGray => new SolidBrush(Color.LightGray);
        public static Brush LightPink => new SolidBrush(Color.LightPink);
        public static Brush LightSalmon => new SolidBrush(Color.LightSalmon);
        public static Brush LightSeaGreen => new SolidBrush(Color.LightSeaGreen);
        public static Brush LightSkyBlue => new SolidBrush(Color.LightSkyBlue);
        public static Brush LightSlateGray => new SolidBrush(Color.LightSlateGray);
        public static Brush LightSteelBlue => new SolidBrush(Color.LightSteelBlue);
        public static Brush LightYellow => new SolidBrush(Color.LightYellow);
        public static Brush Lime => new SolidBrush(Color.Lime);
        public static Brush LimeGreen => new SolidBrush(Color.LimeGreen);
        public static Brush Linen => new SolidBrush(Color.Linen);
        public static Brush Magenta => new SolidBrush(Color.Magenta);
        public static Brush Maroon => new SolidBrush(Color.Maroon);
        public static Brush MediumAquamarine => new SolidBrush(Color.MediumAquamarine);
        public static Brush MediumBlue => new SolidBrush(Color.MediumBlue);
        public static Brush MediumOrchid => new SolidBrush(Color.MediumOrchid);
        public static Brush MediumPurple => new SolidBrush(Color.MediumPurple);
        public static Brush MediumSeaGreen => new SolidBrush(Color.MediumSeaGreen);
        public static Brush MediumSlateBlue => new SolidBrush(Color.MediumSlateBlue);
        public static Brush MediumSpringGreen => new SolidBrush(Color.MediumSpringGreen);
        public static Brush MediumTurquoise => new SolidBrush(Color.MediumTurquoise);
        public static Brush MediumVioletRed => new SolidBrush(Color.MediumVioletRed);
        public static Brush MidnightBlue => new SolidBrush(Color.MidnightBlue);
        public static Brush MintCream => new SolidBrush(Color.MintCream);
        public static Brush MistyRose => new SolidBrush(Color.MistyRose);
        public static Brush Moccasin => new SolidBrush(Color.Moccasin);
        public static Brush NavajoWhite => new SolidBrush(Color.NavajoWhite);
        public static Brush Navy => new SolidBrush(Color.Navy);
        public static Brush OldLace => new SolidBrush(Color.OldLace);
        public static Brush Olive => new SolidBrush(Color.Olive);
        public static Brush OliveDrab => new SolidBrush(Color.OliveDrab);
        public static Brush Orange => new SolidBrush(Color.Orange);
        public static Brush OrangeRed => new SolidBrush(Color.OrangeRed);
        public static Brush Orchid => new SolidBrush(Color.Orchid);
        public static Brush PaleGoldenrod => new SolidBrush(Color.PaleGoldenrod);
        public static Brush PaleGreen => new SolidBrush(Color.PaleGreen);
        public static Brush PaleTurquoise => new SolidBrush(Color.PaleTurquoise);
        public static Brush PaleVioletRed => new SolidBrush(Color.PaleVioletRed);
        public static Brush PapayaWhip => new SolidBrush(Color.PapayaWhip);
        public static Brush PeachPuff => new SolidBrush(Color.PeachPuff);
        public static Brush Peru => new SolidBrush(Color.Peru);
        public static Brush Pink => new SolidBrush(Color.Pink);
        public static Brush Plum => new SolidBrush(Color.Plum);
        public static Brush PowderBlue => new SolidBrush(Color.PowderBlue);
        public static Brush Purple => new SolidBrush(Color.Purple);
        public static Brush RebeccaPurple => new SolidBrush(Color.RebeccaPurple);
        public static Brush Red => new SolidBrush(Color.Red);
        public static Brush RosyBrown => new SolidBrush(Color.RosyBrown);
        public static Brush RoyalBlue => new SolidBrush(Color.RoyalBlue);
        public static Brush SaddleBrown => new SolidBrush(Color.SaddleBrown);
        public static Brush Salmon => new SolidBrush(Color.Salmon);
        public static Brush SandyBrown => new SolidBrush(Color.SandyBrown);
        public static Brush SeaGreen => new SolidBrush(Color.SeaGreen);
        public static Brush SeaShell => new SolidBrush(Color.SeaShell);
        public static Brush Sienna => new SolidBrush(Color.Sienna);
        public static Brush Silver => new SolidBrush(Color.Silver);
        public static Brush SkyBlue => new SolidBrush(Color.SkyBlue);
        public static Brush SlateBlue => new SolidBrush(Color.SlateBlue);
        public static Brush SlateGray => new SolidBrush(Color.SlateGray);
        public static Brush Snow => new SolidBrush(Color.Snow);
        public static Brush SpringGreen => new SolidBrush(Color.SpringGreen);
        public static Brush SteelBlue => new SolidBrush(Color.SteelBlue);
        public static Brush Tan => new SolidBrush(Color.Tan);
        public static Brush Teal => new SolidBrush(Color.Teal);
        public static Brush Thistle => new SolidBrush(Color.Thistle);
        public static Brush Tomato => new SolidBrush(Color.Tomato);
        public static Brush Turquoise => new SolidBrush(Color.Turquoise);
        public static Brush Violet => new SolidBrush(Color.Violet);
        public static Brush Wheat => new SolidBrush(Color.Wheat);
        public static Brush White => new SolidBrush(Color.White);
        public static Brush WhiteSmoke => new SolidBrush(Color.WhiteSmoke);
        public static Brush Yellow => new SolidBrush(Color.Yellow);
        public static Brush YellowGreen => new SolidBrush(Color.YellowGreen);
    }
    public static class Pens
    {
        public static Pen Transparent => new Pen(Color.Transparent);
        public static Pen AliceBlue => new Pen(Color.AliceBlue);
        public static Pen AntiqueWhite => new Pen(Color.AntiqueWhite);
        public static Pen Aqua => new Pen(Color.Aqua);
        public static Pen Aquamarine => new Pen(Color.Aquamarine);
        public static Pen Azure => new Pen(Color.Azure);
        public static Pen Beige => new Pen(Color.Beige);
        public static Pen Bisque => new Pen(Color.Bisque);
        public static Pen Black => new Pen(Color.Black);
        public static Pen BlanchedAlmond => new Pen(Color.BlanchedAlmond);
        public static Pen Blue => new Pen(Color.Blue);
        public static Pen BlueViolet => new Pen(Color.BlueViolet);
        public static Pen Brown => new Pen(Color.Brown);
        public static Pen BurlyWood => new Pen(Color.BurlyWood);
        public static Pen CadetBlue => new Pen(Color.CadetBlue);
        public static Pen Chartreuse => new Pen(Color.Chartreuse);
        public static Pen Chocolate => new Pen(Color.Chocolate);
        public static Pen Coral => new Pen(Color.Coral);
        public static Pen CornflowerBlue => new Pen(Color.CornflowerBlue);
        public static Pen Cornsilk => new Pen(Color.Cornsilk);
        public static Pen Crimson => new Pen(Color.Crimson);
        public static Pen Cyan => new Pen(Color.Cyan);
        public static Pen DarkBlue => new Pen(Color.DarkBlue);
        public static Pen DarkCyan => new Pen(Color.DarkCyan);
        public static Pen DarkGoldenrod => new Pen(Color.DarkGoldenrod);
        public static Pen DarkGray => new Pen(Color.DarkGray);
        public static Pen DarkGreen => new Pen(Color.DarkGreen);
        public static Pen DarkKhaki => new Pen(Color.DarkKhaki);
        public static Pen DarkMagenta => new Pen(Color.DarkMagenta);
        public static Pen DarkOliveGreen => new Pen(Color.DarkOliveGreen);
        public static Pen DarkOrange => new Pen(Color.DarkOrange);
        public static Pen DarkOrchid => new Pen(Color.DarkOrchid);
        public static Pen DarkRed => new Pen(Color.DarkRed);
        public static Pen DarkSalmon => new Pen(Color.DarkSalmon);
        public static Pen DarkSeaGreen => new Pen(Color.DarkSeaGreen);
        public static Pen DarkSlateBlue => new Pen(Color.DarkSlateBlue);
        public static Pen DarkSlateGray => new Pen(Color.DarkSlateGray);
        public static Pen DarkTurquoise => new Pen(Color.DarkTurquoise);
        public static Pen DarkViolet => new Pen(Color.DarkViolet);
        public static Pen DeepPink => new Pen(Color.DeepPink);
        public static Pen DeepSkyBlue => new Pen(Color.DeepSkyBlue);
        public static Pen DimGray => new Pen(Color.DimGray);
        public static Pen DodgerBlue => new Pen(Color.DodgerBlue);
        public static Pen Firebrick => new Pen(Color.Firebrick);
        public static Pen FloralWhite => new Pen(Color.FloralWhite);
        public static Pen ForestGreen => new Pen(Color.ForestGreen);
        public static Pen Fuchsia => new Pen(Color.Fuchsia);
        public static Pen Gainsboro => new Pen(Color.Gainsboro);
        public static Pen GhostWhite => new Pen(Color.GhostWhite);
        public static Pen Gold => new Pen(Color.Gold);
        public static Pen Goldenrod => new Pen(Color.Goldenrod);
        public static Pen Gray => new Pen(Color.Gray);
        public static Pen Green => new Pen(Color.Green);
        public static Pen GreenYellow => new Pen(Color.GreenYellow);
        public static Pen Honeydew => new Pen(Color.Honeydew);
        public static Pen HotPink => new Pen(Color.HotPink);
        public static Pen IndianRed => new Pen(Color.IndianRed);
        public static Pen Indigo => new Pen(Color.Indigo);
        public static Pen Ivory => new Pen(Color.Ivory);
        public static Pen Khaki => new Pen(Color.Khaki);
        public static Pen Lavender => new Pen(Color.Lavender);
        public static Pen LavenderBlush => new Pen(Color.LavenderBlush);
        public static Pen LawnGreen => new Pen(Color.LawnGreen);
        public static Pen LemonChiffon => new Pen(Color.LemonChiffon);
        public static Pen LightBlue => new Pen(Color.LightBlue);
        public static Pen LightCoral => new Pen(Color.LightCoral);
        public static Pen LightCyan => new Pen(Color.LightCyan);
        public static Pen LightGoldenrodYellow => new Pen(Color.LightGoldenrodYellow);
        public static Pen LightGreen => new Pen(Color.LightGreen);
        public static Pen LightGray => new Pen(Color.LightGray);
        public static Pen LightPink => new Pen(Color.LightPink);
        public static Pen LightSalmon => new Pen(Color.LightSalmon);
        public static Pen LightSeaGreen => new Pen(Color.LightSeaGreen);
        public static Pen LightSkyBlue => new Pen(Color.LightSkyBlue);
        public static Pen LightSlateGray => new Pen(Color.LightSlateGray);
        public static Pen LightSteelBlue => new Pen(Color.LightSteelBlue);
        public static Pen LightYellow => new Pen(Color.LightYellow);
        public static Pen Lime => new Pen(Color.Lime);
        public static Pen LimeGreen => new Pen(Color.LimeGreen);
        public static Pen Linen => new Pen(Color.Linen);
        public static Pen Magenta => new Pen(Color.Magenta);
        public static Pen Maroon => new Pen(Color.Maroon);
        public static Pen MediumAquamarine => new Pen(Color.MediumAquamarine);
        public static Pen MediumBlue => new Pen(Color.MediumBlue);
        public static Pen MediumOrchid => new Pen(Color.MediumOrchid);
        public static Pen MediumPurple => new Pen(Color.MediumPurple);
        public static Pen MediumSeaGreen => new Pen(Color.MediumSeaGreen);
        public static Pen MediumSlateBlue => new Pen(Color.MediumSlateBlue);
        public static Pen MediumSpringGreen => new Pen(Color.MediumSpringGreen);
        public static Pen MediumTurquoise => new Pen(Color.MediumTurquoise);
        public static Pen MediumVioletRed => new Pen(Color.MediumVioletRed);
        public static Pen MidnightBlue => new Pen(Color.MidnightBlue);
        public static Pen MintCream => new Pen(Color.MintCream);
        public static Pen MistyRose => new Pen(Color.MistyRose);
        public static Pen Moccasin => new Pen(Color.Moccasin);
        public static Pen NavajoWhite => new Pen(Color.NavajoWhite);
        public static Pen Navy => new Pen(Color.Navy);
        public static Pen OldLace => new Pen(Color.OldLace);
        public static Pen Olive => new Pen(Color.Olive);
        public static Pen OliveDrab => new Pen(Color.OliveDrab);
        public static Pen Orange => new Pen(Color.Orange);
        public static Pen OrangeRed => new Pen(Color.OrangeRed);
        public static Pen Orchid => new Pen(Color.Orchid);
        public static Pen PaleGoldenrod => new Pen(Color.PaleGoldenrod);
        public static Pen PaleGreen => new Pen(Color.PaleGreen);
        public static Pen PaleTurquoise => new Pen(Color.PaleTurquoise);
        public static Pen PaleVioletRed => new Pen(Color.PaleVioletRed);
        public static Pen PapayaWhip => new Pen(Color.PapayaWhip);
        public static Pen PeachPuff => new Pen(Color.PeachPuff);
        public static Pen Peru => new Pen(Color.Peru);
        public static Pen Pink => new Pen(Color.Pink);
        public static Pen Plum => new Pen(Color.Plum);
        public static Pen PowderBlue => new Pen(Color.PowderBlue);
        public static Pen Purple => new Pen(Color.Purple);
        public static Pen RebeccaPurple => new Pen(Color.RebeccaPurple);
        public static Pen Red => new Pen(Color.Red);
        public static Pen RosyBrown => new Pen(Color.RosyBrown);
        public static Pen RoyalBlue => new Pen(Color.RoyalBlue);
        public static Pen SaddleBrown => new Pen(Color.SaddleBrown);
        public static Pen Salmon => new Pen(Color.Salmon);
        public static Pen SandyBrown => new Pen(Color.SandyBrown);
        public static Pen SeaGreen => new Pen(Color.SeaGreen);
        public static Pen SeaShell => new Pen(Color.SeaShell);
        public static Pen Sienna => new Pen(Color.Sienna);
        public static Pen Silver => new Pen(Color.Silver);
        public static Pen SkyBlue => new Pen(Color.SkyBlue);
        public static Pen SlateBlue => new Pen(Color.SlateBlue);
        public static Pen SlateGray => new Pen(Color.SlateGray);
        public static Pen Snow => new Pen(Color.Snow);
        public static Pen SpringGreen => new Pen(Color.SpringGreen);
        public static Pen SteelBlue => new Pen(Color.SteelBlue);
        public static Pen Tan => new Pen(Color.Tan);
        public static Pen Teal => new Pen(Color.Teal);
        public static Pen Thistle => new Pen(Color.Thistle);
        public static Pen Tomato => new Pen(Color.Tomato);
        public static Pen Turquoise => new Pen(Color.Turquoise);
        public static Pen Violet => new Pen(Color.Violet);
        public static Pen Wheat => new Pen(Color.Wheat);
        public static Pen White => new Pen(Color.White);
        public static Pen WhiteSmoke => new Pen(Color.WhiteSmoke);
        public static Pen Yellow => new Pen(Color.Yellow);
        public static Pen YellowGreen => new Pen(Color.YellowGreen);
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
        public Font(FontFamily family, float emSize) : this(family.Name, emSize, FontStyle.Regular) { }
        public Font(FontFamily family, float emSize, FontStyle style) : this(family.Name, emSize, style) { }
        public Font(FontFamily family, float emSize, FontStyle style, GraphicsUnit unit) : this(family.Name, emSize, style) { }
        public Font(FontFamily family, float emSize, GraphicsUnit unit) : this(family.Name, emSize, FontStyle.Regular) { }
        public Font(string familyName, float emSize, GraphicsUnit unit) : this(familyName, emSize, FontStyle.Regular) { }
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
        /// <summary>An image read from a stream (PNG, JPEG, BMP, GIF): its encoded bytes and pixel size.</summary>
        public static Image FromStream(System.IO.Stream stream)
        {
            var buffer = new System.IO.MemoryStream();
            stream.CopyTo(buffer);
            return new EncodedImage(buffer.ToArray());
        }
        public static Image FromFile(string filename) => new EncodedImage(System.IO.File.ReadAllBytes(filename));
        public int Width { get; protected set; }
        public int Height { get; protected set; }
        public Size Size => new Size(Width, Height);
        public object Tag { get; set; }
        public abstract object Clone();
        public void Dispose() { }
    }
    /// <summary>A bitmap by reference (an original resource image) or of a size (drawn by the renderer).</summary>
    public class Bitmap : Image
    {
        protected Bitmap() { }
        public Bitmap(int width, int height) { Width = width; Height = height; }
        public Bitmap(Image original) { Width = original?.Width ?? 0; Height = original?.Height ?? 0; Source = original; }
        public Bitmap(Image original, int width, int height) { Width = width; Height = height; Source = original; }
        public Bitmap(int width, int height, System.Drawing.Imaging.PixelFormat format) : this(width, height) { PixelFormat = format; }
        public System.Drawing.Imaging.PixelFormat PixelFormat { get; } = System.Drawing.Imaging.PixelFormat.Format32bppArgb;
        /// <summary>What was drawn on the bitmap (Graphics.FromImage); the renderer rasterizes it.</summary>
        public Graphics Drawing { get; internal set; }
        /// <summary>The image this bitmap was made from, if any.</summary>
        public Image Source { get; }
        public override object Clone() => MemberwiseClone();
    }
    /// <summary>An encoded image (file bytes); the pixel size is read from the PNG, GIF, BMP or JPEG header.</summary>
    public sealed class EncodedImage : Bitmap
    {
        public EncodedImage(byte[] bytes)
        {
            Bytes = bytes ?? throw new ArgumentNullException(nameof(bytes));
            (int w, int h) = ReadSize(bytes);
            Width = w; Height = h;
        }
        public byte[] Bytes { get; }
        static (int, int) ReadSize(byte[] b)
        {
            int Be32(int i) => (b[i] << 24) | (b[i + 1] << 16) | (b[i + 2] << 8) | b[i + 3];
            if (b.Length >= 24 && b[0] == 0x89 && b[1] == (byte)'P' && b[2] == (byte)'N' && b[3] == (byte)'G') return (Be32(16), Be32(20));
            if (b.Length >= 10 && b[0] == (byte)'G' && b[1] == (byte)'I' && b[2] == (byte)'F') return (b[6] | (b[7] << 8), b[8] | (b[9] << 8));
            if (b.Length >= 26 && b[0] == (byte)'B' && b[1] == (byte)'M') return (BitConverter.ToInt32(b, 18), Math.Abs(BitConverter.ToInt32(b, 22)));
            if (b.Length >= 4 && b[0] == 0xFF && b[1] == 0xD8)
            {
                int i = 2;
                while (i + 9 < b.Length)
                {
                    if (b[i] != 0xFF) { i++; continue; }
                    byte marker = b[i + 1];
                    int length = (b[i + 2] << 8) | b[i + 3];
                    if (marker >= 0xC0 && marker <= 0xCF && marker != 0xC4 && marker != 0xC8 && marker != 0xCC)
                        return ((b[i + 7] << 8) | b[i + 8], (b[i + 5] << 8) | b[i + 6]);
                    i += 2 + length;
                }
            }
            return (0, 0);
        }
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
    public enum LinearGradientMode { Horizontal, Vertical, ForwardDiagonal, BackwardDiagonal }
    /// <summary>A two-colour linear gradient between two points (the renderer replays it as a linear gradient).</summary>
    public sealed class LinearGradientBrush : Brush
    {
        public LinearGradientBrush(PointF point1, PointF point2, Color color1, Color color2) { Start = point1; End = point2; LinearColors = new[] { color1, color2 }; }
        public LinearGradientBrush(Point point1, Point point2, Color color1, Color color2) : this(new PointF(point1.X, point1.Y), new PointF(point2.X, point2.Y), color1, color2) { }
        public LinearGradientBrush(RectangleF rect, Color color1, Color color2, LinearGradientMode linearGradientMode)
            : this(rect.Location, linearGradientMode == LinearGradientMode.Horizontal ? new PointF(rect.Right, rect.Top) :
                                  linearGradientMode == LinearGradientMode.Vertical ? new PointF(rect.Left, rect.Bottom) :
                                  linearGradientMode == LinearGradientMode.ForwardDiagonal ? new PointF(rect.Right, rect.Bottom) : new PointF(rect.Left, rect.Bottom), color1, color2) { }
        public LinearGradientBrush(Rectangle rect, Color color1, Color color2, LinearGradientMode linearGradientMode)
            : this(new RectangleF(rect.X, rect.Y, rect.Width, rect.Height), color1, color2, linearGradientMode) { }
        public LinearGradientBrush(Rectangle rect, Color color1, Color color2, float angle) : this(rect, color1, color2, LinearGradientMode.Horizontal) { Angle = angle; }
        public PointF Start { get; }
        public PointF End { get; }
        public float Angle { get; }
        public Color[] LinearColors { get; set; }
        public override object Clone() => MemberwiseClone();
    }
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
    public enum PixelFormat
    {
        Undefined = 0, DontCare = 0, Format16bppRgb555 = 135173, Format16bppRgb565 = 135174, Format24bppRgb = 137224,
        Format32bppRgb = 139273, Format1bppIndexed = 196865, Format4bppIndexed = 197634, Format8bppIndexed = 198659,
        Format16bppArgb1555 = 397319, Format32bppPArgb = 925707, Format16bppGrayScale = 1052676, Format48bppRgb = 1060876,
        Format64bppPArgb = 1851406, Format32bppArgb = 2498570, Format64bppArgb = 3424269,
    }
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
