// What the original draws itself: the recorded GDI+ calls of a Paint handler (System.Drawing.Graphics of
// X/Domain/WinFormsCompat/Painting.cs) replayed on Avalonia's DrawingContext, and ZedGraph plots drawn from their pane
// (ports of replay/PaintedControl in X/UI/original_controls.py and GraphWidget in original_forms.py).
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using WinForms = System.Windows.Forms;
using D = System.Drawing;

namespace PrePoMaxX.FrontEnd
{
    internal static class Painting
    {
        static Color C(D.Color color) => Ui.ToColor(color);
        static Rect R(D.RectangleF r) => new Rect(r.X, r.Y, r.Width, r.Height);
        static Point P(D.PointF p) => new Point(p.X, p.Y);

        static IDashStyle Dash(D.Drawing2D.DashStyle style)
        {
            switch (style)
            {
                case D.Drawing2D.DashStyle.Dash: return DashStyle.Dash;
                case D.Drawing2D.DashStyle.Dot: return DashStyle.Dot;
                case D.Drawing2D.DashStyle.DashDot: return DashStyle.DashDot;
                case D.Drawing2D.DashStyle.DashDotDot: return DashStyle.DashDotDot;
                default: return null;
            }
        }

        internal static Pen Pen(D.Pen pen) =>
            new Pen(new SolidColorBrush(C(pen.Color)), pen.Width > 0 ? Math.Max(1.0, pen.Width) : 1.0, Dash(pen.DashStyle), PenLineCap.Flat);

        internal static IBrush Brush(D.Brush brush)
        {
            if (brush is D.Drawing2D.LinearGradientBrush gradient && gradient.LinearColors != null && gradient.LinearColors.Length > 0)
                return new LinearGradientBrush
                {
                    StartPoint = new RelativePoint(gradient.Start.X, gradient.Start.Y, RelativeUnit.Absolute),
                    EndPoint = new RelativePoint(gradient.End.X, gradient.End.Y, RelativeUnit.Absolute),
                    GradientStops = { new GradientStop(C(gradient.LinearColors[0]), 0), new GradientStop(C(gradient.LinearColors[gradient.LinearColors.Length - 1]), 1) },
                };
            return brush is D.SolidBrush solid ? new SolidColorBrush(C(solid.Color)) : Brushes.Black;
        }

        static Typeface Typeface(D.Font font) => new Typeface(FontFamily.Default, font != null && font.Italic ? FontStyle.Italic : FontStyle.Normal,
                                                              font != null && font.Bold ? FontWeight.Bold : FontWeight.Normal);
        static double FontPixels(D.Font font) => Math.Max(1, Math.Round((font?.Size ?? 9f) * 96 / 72));

        /// <summary>GDI+ AdjustableArrowCap at the end of a line: a triangle Width x Height pen widths, its tip on the end.</summary>
        static void ArrowCap(DrawingContext context, D.Pen pen, Point start, Point end)
        {
            if (!(pen.CustomEndCap is D.Drawing2D.AdjustableArrowCap cap)) return;
            double width = Math.Max(pen.Width, 1.0);
            double dx = end.X - start.X, dy = end.Y - start.Y, length = Math.Sqrt(dx * dx + dy * dy);
            if (length == 0) return;
            double ux = dx / length, uy = dy / length, back = cap.Height * width, half = cap.Width * width / 2;
            var b = new Point(end.X - ux * back, end.Y - uy * back);
            var geometry = new PolylineGeometry(new[] { end, new Point(b.X - uy * half, b.Y + ux * half), new Point(b.X + uy * half, b.Y - ux * half) }, true);
            context.DrawGeometry(new SolidColorBrush(C(pen.Color)), null, geometry);
        }

        static Geometry PathGeometry(D.Drawing2D.GraphicsPath path)
        {
            var geometry = new StreamGeometry();
            using (StreamGeometryContext g = geometry.Open())
            {
                bool open = false;
                void Line(Point a, Point b) { if (!open) { g.BeginFigure(a, true); open = true; } else g.LineTo(a); g.LineTo(b); }
                foreach (var part in path.Parts)
                {
                    object[] a = part.Arguments;
                    switch (part.Name)
                    {
                        case "Line": Line(P((D.PointF)a[0]), P((D.PointF)a[1])); break;
                        case "Lines": case "Polygon":
                        {
                            var points = (D.PointF[])a[0];
                            if (points.Length == 0) break;
                            if (part.Name == "Polygon" && open) { g.EndFigure(false); open = false; }
                            if (!open) { g.BeginFigure(P(points[0]), true); open = true; } else g.LineTo(P(points[0]));
                            foreach (var p in points.Skip(1)) g.LineTo(P(p));
                            if (part.Name == "Polygon") { g.EndFigure(true); open = false; }
                            break;
                        }
                        case "Rectangle": case "Ellipse": case "Arc":
                        {
                            var r = (D.RectangleF)a[0];
                            double start = part.Name == "Arc" ? (float)a[1] : 0, sweep = part.Name == "Arc" ? (float)a[2] : 360;
                            if (part.Name == "Rectangle")
                            {
                                if (open) { g.EndFigure(false); open = false; }
                                g.BeginFigure(new Point(r.Left, r.Top), true); g.LineTo(new Point(r.Right, r.Top)); g.LineTo(new Point(r.Right, r.Bottom)); g.LineTo(new Point(r.Left, r.Bottom));
                                g.EndFigure(true);
                                break;
                            }
                            // Arcs flattened (GDI+ angles: degrees clockwise from the x axis)
                            int steps = Math.Max(4, (int)(Math.Abs(sweep) / 6));
                            for (int i = 0; i <= steps; i++)
                            {
                                double t = (start + sweep * i / steps) * Math.PI / 180;
                                var p = new Point(r.X + r.Width / 2 + r.Width / 2 * Math.Cos(t), r.Y + r.Height / 2 + r.Height / 2 * Math.Sin(t));
                                if (!open) { g.BeginFigure(p, true); open = true; } else g.LineTo(p);
                            }
                            if (part.Name == "Ellipse") { g.EndFigure(true); open = false; }
                            break;
                        }
                        case "Close": if (open) { g.EndFigure(true); open = false; } break;
                        case "Start": if (open) { g.EndFigure(false); open = false; } break;
                    }
                }
                if (open) g.EndFigure(false);
            }
            return geometry;
        }

        /// <summary>Draws the commands of a recording System.Drawing.Graphics.</summary>
        internal static void Replay(DrawingContext context, IReadOnlyList<D.PaintCommand> commands, Size size)
        {
            // GDI+ Save/Restore and the clip and transforms: Avalonia's pushed states, unwound in order
            var states = new Stack<List<IDisposable>>();
            var current = new List<IDisposable>();
            void Push(IDisposable state) => current.Add(state);
            void Unwind(List<IDisposable> list) { for (int i = list.Count - 1; i >= 0; i--) list[i].Dispose(); list.Clear(); }
            Matrix transform = Matrix.Identity;
            try
            {
                foreach (D.PaintCommand command in commands)
                {
                    object[] a = command.Arguments;
                    switch (command.Name)
                    {
                        case "Save": states.Push(current); current = new List<IDisposable>(); break;
                        case "Restore": Unwind(current); current = states.Count > 0 ? states.Pop() : new List<IDisposable>(); break;
                        case "SetClip": Push(context.PushClip(R((D.RectangleF)a[0]))); break;
                        case "ResetClip": break;
                        case "TranslateTransform": Push(context.PushTransform(Matrix.CreateTranslation((float)a[0], (float)a[1]))); break;
                        case "RotateTransform": Push(context.PushTransform(Matrix.CreateRotation((float)a[0] * Math.PI / 180))); break;
                        case "ScaleTransform": Push(context.PushTransform(Matrix.CreateScale((float)a[0], (float)a[1]))); break;
                        case "ResetTransform": Unwind(current); break;
                        case "Clear": context.FillRectangle(new SolidColorBrush(C((D.Color)a[0])), new Rect(size)); break;
                        case "FillRectangle": context.FillRectangle(Brush((D.Brush)a[0]), R((D.RectangleF)a[1])); break;
                        case "DrawRectangle": context.DrawRectangle(null, Pen((D.Pen)a[0]), R((D.RectangleF)a[1])); break;
                        case "DrawEllipse": { var r = R((D.RectangleF)a[1]); context.DrawEllipse(null, Pen((D.Pen)a[0]), r.Center, r.Width / 2, r.Height / 2); break; }
                        case "FillEllipse": { var r = R((D.RectangleF)a[1]); context.DrawEllipse(Brush((D.Brush)a[0]), null, r.Center, r.Width / 2, r.Height / 2); break; }
                        case "DrawLine":
                        {
                            var pen = (D.Pen)a[0];
                            Point start = P((D.PointF)a[1]), end = P((D.PointF)a[2]);
                            context.DrawLine(Pen(pen), start, end);
                            ArrowCap(context, pen, start, end);
                            break;
                        }
                        case "DrawLines": context.DrawGeometry(null, Pen((D.Pen)a[0]), new PolylineGeometry(((D.PointF[])a[1]).Select(P), false)); break;
                        case "DrawPolygon": context.DrawGeometry(null, Pen((D.Pen)a[0]), new PolylineGeometry(((D.PointF[])a[1]).Select(P), true)); break;
                        case "FillPolygon": context.DrawGeometry(Brush((D.Brush)a[0]), null, new PolylineGeometry(((D.PointF[])a[1]).Select(P), true)); break;
                        case "DrawPath": context.DrawGeometry(null, Pen((D.Pen)a[0]), PathGeometry((D.Drawing2D.GraphicsPath)a[1])); break;
                        case "FillPath": context.DrawGeometry(Brush((D.Brush)a[0]), null, PathGeometry((D.Drawing2D.GraphicsPath)a[1])); break;
                        case "DrawImage":
                        {
                            Bitmap bitmap = Ui.Bitmap((D.Image)a[0]);
                            if (bitmap != null) context.DrawImage(bitmap, R((D.RectangleF)a[1]));
                            break;
                        }
                        case "DrawText": case "DrawString":
                        {
                            string text = (string)a[0];
                            var font = a[1] as D.Font;
                            D.RectangleF box;
                            IBrush brush;
                            int flags = 0;
                            if (command.Name == "DrawText") { box = (D.RectangleF)a[2]; brush = new SolidColorBrush(C((D.Color)a[3])); flags = (int)a[4]; }
                            else { box = (D.RectangleF)a[3]; brush = Brush((D.Brush)a[2]); }
                            var formatted = new FormattedText(text, CultureInfo.CurrentCulture, FlowDirection.LeftToRight, Typeface(font), FontPixels(font), brush);
                            double x = box.X, y = box.Y;
                            if (box.Width > 0 && box.Height > 0)
                            {
                                var format = command.Name == "DrawString" ? a[4] as D.StringFormat : null;
                                bool hCenter = (flags & (int)WinForms.TextFormatFlags.HorizontalCenter) != 0 || format?.Alignment == D.StringAlignment.Center;
                                bool right = (flags & (int)WinForms.TextFormatFlags.Right) != 0 || format?.Alignment == D.StringAlignment.Far;
                                bool vCenter = (flags & (int)WinForms.TextFormatFlags.VerticalCenter) != 0 || format?.LineAlignment == D.StringAlignment.Center;
                                bool bottom = (flags & (int)WinForms.TextFormatFlags.Bottom) != 0 || format?.LineAlignment == D.StringAlignment.Far;
                                formatted.MaxTextWidth = box.Width;
                                formatted.TextAlignment = hCenter ? TextAlignment.Center : right ? TextAlignment.Right : TextAlignment.Left;
                                if (vCenter) y = box.Y + (box.Height - formatted.Height) / 2;
                                else if (bottom) y = box.Bottom - formatted.Height;
                            }
                            context.DrawText(formatted, new Point(x, y));
                            break;
                        }
                    }
                }
            }
            finally
            {
                Unwind(current);
                while (states.Count > 0) { current = states.Pop(); Unwind(current); }
            }
        }
    }

    /// <summary>A control that paints itself (a Paint handler, e.g. FrmSection's layup diagram): the model paints
    /// (Control.RenderPaint) and the recorded calls are replayed; the mouse reaches the control as WinForms raises it.
    /// Its children are mirrored above it.</summary>
    internal sealed class PaintedView : Control, IMirror
    {
        readonly WinForms.Control _control;
        WinForms.MouseButtons _pressed;
        public PaintedView(WinForms.Control control) { _control = control; ClipToBounds = true; }
        public void Update() => InvalidateVisual();
        public void Refresh(string property) => InvalidateVisual();

        public override void Render(DrawingContext context)
        {
            D.Graphics graphics = Ui.Guard(() => _control.RenderPaint());
            if (_control.BackColor.A > 0) context.FillRectangle(Ui.Brush(_control.BackColor), new Rect(Bounds.Size));
            if (graphics != null) Painting.Replay(context, graphics.Commands, Bounds.Size);
        }

        protected override void OnPointerPressed(PointerPressedEventArgs e)
        {
            Point p = e.GetPosition(this);
            _pressed = Keyboard.Button(e.GetCurrentPoint(this).Properties.PointerUpdateKind);
            var button = _pressed;
            Ui.Input(() => _control.RaiseMouse("down", button, 1, (int)p.X, (int)p.Y));
            InvalidateVisual();
        }
        protected override void OnPointerReleased(PointerReleasedEventArgs e)
        {
            Point p = e.GetPosition(this);
            var button = Keyboard.Button(e.GetCurrentPoint(this).Properties.PointerUpdateKind);
            bool clicked = _pressed == button && new Rect(Bounds.Size).Contains(p);
            _pressed = WinForms.MouseButtons.None;
            Ui.Input(() =>
            {
                if (clicked) { _control.RaiseClick(); _control.RaiseMouse("click", button, 1, (int)p.X, (int)p.Y); }
                _control.RaiseMouse("up", button, 1, (int)p.X, (int)p.Y);
            });
            InvalidateVisual();
        }
        protected override void OnPointerMoved(PointerEventArgs e)
        {
            Point p = e.GetPosition(this);
            Ui.Input(() => _control.RaiseMouse("move", _pressed, 0, (int)p.X, (int)p.Y));
        }
    }

    /// <summary>ZedGraphControl drawn from its pane: the axis ranges and major steps the original code and AxisChange
    /// set (linear or log, X, Y and Y2), grids, curves (line style, circle symbols, missing points break the line),
    /// axis titles and the legend.</summary>
    internal sealed class GraphView : Control, IMirror
    {
        readonly ZedGraph.ZedGraphControl _control;
        public GraphView(ZedGraph.ZedGraphControl control) { _control = control; ClipToBounds = true; }
        public void Update() => InvalidateVisual();
        public void Refresh(string property) => InvalidateVisual();

        static Func<double, double> Map(ZedGraph.Scale scale, double low, double high, bool log)
        {
            double a = scale.Min, b = scale.Max;
            if (log)
            {
                a = Math.Log10(Math.Max(a, 1e-300)); b = Math.Log10(Math.Max(b, 1e-300));
                if (b <= a) b = a + 1;
                return v => v > 0 ? low + (Math.Log10(v) - a) / (b - a) * (high - low) : double.NaN;
            }
            if (b <= a) b = a + 1;
            return v => low + (v - a) / (b - a) * (high - low);
        }

        static List<double> Ticks(ZedGraph.Scale scale, bool log)
        {
            double a = scale.Min, b = scale.Max, step = scale.MajorStep;
            var values = new List<double>();
            if (log)
            {
                int first = (int)Math.Ceiling(Math.Log10(Math.Max(a, 1e-300)) - 1e-9), last = (int)Math.Floor(Math.Log10(Math.Max(b, 1e-300)) + 1e-9);
                int s = Math.Max(1, (int)Math.Round(step));
                for (int e = first; e <= last && values.Count < 200; e += s) values.Add(Math.Pow(10, e));
                return values;
            }
            if (!(step > 0) || double.IsInfinity(step) || (b - a) / step > 500) return new List<double> { a, b };
            double start = scale.BaseTic != double.MaxValue && !double.IsInfinity(scale.BaseTic) ? scale.BaseTic : Math.Ceiling(a / step - 1e-9) * step;
            while (start - step >= a - 1e-9 * step) start -= step;
            for (double v = start; v <= b + 1e-9 * step && values.Count < 500; v += step) values.Add(Math.Abs(v) < 1e-12 * step ? 0 : v);
            return values;
        }

        static string Label(double value, double step, bool log)
        {
            if (log || step <= 0 || double.IsInfinity(step)) return value.ToString("G", CultureInfo.InvariantCulture);
            int digits = step < 1 ? Math.Max(0, -(int)Math.Floor(Math.Log10(step))) : 0;
            return value.ToString("F" + digits, CultureInfo.InvariantCulture);
        }

        static IBrush B(D.Color color, IBrush fallback = null) => color.IsEmpty || color.A == 0 ? fallback ?? Brushes.Black : Ui.Brush(color);
        static FormattedText Text(string text, IBrush brush, bool bold = false) =>
            new FormattedText(text ?? "", CultureInfo.CurrentCulture, FlowDirection.LeftToRight, bold ? new Typeface(FontFamily.Default, FontStyle.Normal, FontWeight.Bold) : Look.Typeface, Look.FontSize, brush);

        public override void Render(DrawingContext context)
        {
            ZedGraph.GraphPane pane = _control.GraphPane;
            var curves = pane.CurveList.Cast<ZedGraph.CurveItem>().Where(c => c.IsVisible).ToList();
            context.FillRectangle(pane.Fill.Type != ZedGraph.FillType.None ? B(pane.Fill.Color, Brushes.White) : Brushes.White, new Rect(Bounds.Size));
            double lineHeight = Text("Xg", Brushes.Black).Height;
            bool y2 = pane.Y2Axis.IsVisible;
            bool legend = pane.Legend.IsVisible && curves.Count > 0;
            double top = 12 + (legend ? lineHeight + 8 : 0);
            string xTitle = pane.XAxis.Title.Text ?? "";
            int titleLines = Math.Max(1, xTitle.Split('\n').Length);
            double left = 70, right = y2 ? 70 : 20, bottom = (1 + titleLines) * lineHeight + 16;
            var plot = new Rect(left, top, Math.Max(10, Bounds.Width - left - right), Math.Max(10, Bounds.Height - top - bottom));
            context.FillRectangle(B(pane.Chart.Fill.Color, Brushes.White), plot);
            bool logX = pane.XAxis.Type == ZedGraph.AxisType.Log, logY = pane.YAxis.Type == ZedGraph.AxisType.Log, logY2 = pane.Y2Axis.Type == ZedGraph.AxisType.Log;
            var px = Map(pane.XAxis.Scale, plot.Left, plot.Right, logX);
            var py = Map(pane.YAxis.Scale, plot.Bottom, plot.Top, logY);
            var py2 = Map(pane.Y2Axis.Scale, plot.Bottom, plot.Top, logY2);
            var xt = Ticks(pane.XAxis.Scale, logX); var yt = Ticks(pane.YAxis.Scale, logY);
            var y2t = y2 ? Ticks(pane.Y2Axis.Scale, logY2) : new List<double>();
            // Grids (dotted, as ZedGraph's dash 1/5)
            var dotted = new DashStyle(new double[] { 1, 5 }, 0);
            if (pane.XAxis.MajorGrid.IsVisible)
                foreach (double v in xt) { double p = px(v); if (!double.IsNaN(p)) context.DrawLine(new Pen(B(pane.XAxis.MajorGrid.Color), 1, dotted), new Point(p, plot.Top), new Point(p, plot.Bottom)); }
            if (pane.YAxis.MajorGrid.IsVisible)
                foreach (double v in yt) { double p = py(v); if (!double.IsNaN(p)) context.DrawLine(new Pen(B(pane.YAxis.MajorGrid.Color), 1, dotted), new Point(plot.Left, p), new Point(plot.Right, p)); }
            var black = new Pen(Brushes.Black, 1);
            context.DrawRectangle(null, black, plot);
            foreach (double v in xt)
            {
                double p = px(v);
                if (double.IsNaN(p)) continue;
                context.DrawLine(black, new Point(p, plot.Bottom), new Point(p, plot.Bottom - 5));
                var t = Text(Label(v, pane.XAxis.Scale.MajorStep, logX), Brushes.Black);
                context.DrawText(t, new Point(p - t.Width / 2, plot.Bottom + 4));
            }
            foreach (double v in yt)
            {
                double p = py(v);
                if (double.IsNaN(p)) continue;
                context.DrawLine(black, new Point(plot.Left, p), new Point(plot.Left + 5, p));
                var t = Text(Label(v, pane.YAxis.Scale.MajorStep, logY), Brushes.Black);
                context.DrawText(t, new Point(plot.Left - t.Width - 6, p - t.Height / 2));
            }
            foreach (double v in y2t)
            {
                double p = py2(v);
                if (double.IsNaN(p)) continue;
                context.DrawLine(black, new Point(plot.Right, p), new Point(plot.Right - 5, p));
                var t = Text(Label(v, pane.Y2Axis.Scale.MajorStep, logY2), Brushes.Black);
                context.DrawText(t, new Point(plot.Right + 6, p - t.Height / 2));
            }
            var title = Text(xTitle, Brushes.Black, true);
            title.MaxTextWidth = plot.Width; title.TextAlignment = TextAlignment.Center;
            context.DrawText(title, new Point(plot.Left, plot.Bottom + lineHeight + 6));
            foreach (var (text, x, angle) in new[] { (pane.YAxis.Title.Text ?? "", 14.0, -90.0), (y2 ? pane.Y2Axis.Title.Text ?? "" : "", Bounds.Width - 14, 90.0) })
            {
                if (string.IsNullOrEmpty(text)) continue;
                var t = Text(text, Brushes.Black, true);
                t.MaxTextWidth = plot.Height; t.TextAlignment = TextAlignment.Center;
                using (context.PushTransform(Matrix.CreateTranslation(-plot.Height / 2, -lineHeight / 2) * Matrix.CreateRotation(angle * Math.PI / 180) * Matrix.CreateTranslation(x, plot.Center.Y)))
                    context.DrawText(t, new Point(0, 0));
            }
            using (context.PushClip(plot.Inflate(4)))
                foreach (var curve in curves)
                {
                    IBrush color = B(curve.Color);
                    var line = (curve as ZedGraph.LineItem)?.Line;
                    var pen = new Pen(color, line?.Width ?? 1, line != null ? Painting.Pen(new D.Pen(curve.Color) { DashStyle = line.Style }).DashStyle : null);
                    var map = curve.IsY2Axis ? py2 : py;
                    var segments = new List<List<Point>>();
                    var segment = new List<Point>();
                    for (int i = 0; i < curve.Points.Count; i++)
                    {
                        var point = curve.Points[i];
                        double x = point.X, y = point.Y;
                        if (x == double.MaxValue || y == double.MaxValue || double.IsNaN(x) || double.IsNaN(y) || double.IsInfinity(x) || double.IsInfinity(y))
                        {
                            if (segment.Count > 0) segments.Add(segment);
                            segment = new List<Point>();
                            continue;
                        }
                        double qx = px(x), qy = map(y);
                        if (double.IsNaN(qx) || double.IsNaN(qy) || double.IsInfinity(qx) || double.IsInfinity(qy)) continue;
                        segment.Add(new Point(qx, qy));
                    }
                    if (segment.Count > 0) segments.Add(segment);
                    if (line == null || line.IsVisible)
                        foreach (var s in segments) if (s.Count > 1) context.DrawGeometry(null, pen, new PolylineGeometry(s, false));
                    var symbol = (curve as ZedGraph.LineItem)?.Symbol;
                    if (symbol != null && symbol.IsVisible && symbol.Type != ZedGraph.SymbolType.None)
                    {
                        IBrush fill = symbol.Fill.Type != ZedGraph.FillType.None ? B(symbol.Fill.Color, Brushes.White) : Brushes.White;
                        double radius = symbol.Size / 2.0;
                        foreach (var s in segments) foreach (var p in s) context.DrawEllipse(fill, new Pen(color, 1), p, radius, radius);
                    }
                }
            if (legend)
            {
                var entries = curves.Where(c => !string.IsNullOrEmpty(c.Label.Text)).Select(c => (B(c.Color), Text(c.Label.Text, Brushes.Black))).ToList();
                double total = entries.Sum(e => 34 + e.Item2.Width + 12);
                double x = pane.Legend.Position == ZedGraph.LegendPos.TopCenter ? plot.Center.X - total / 2 : plot.Left;
                double y = 8 + lineHeight / 2;
                foreach (var (color, text) in entries)
                {
                    context.DrawLine(new Pen(color, 1), new Point(x, y), new Point(x + 28, y));
                    context.DrawEllipse(Brushes.White, new Pen(color, 1), new Point(x + 14, y), 3.5, 3.5);
                    context.DrawText(text, new Point(x + 34, y - text.Height / 2));
                    x += 34 + text.Width + 12;
                }
            }
        }
    }
}
