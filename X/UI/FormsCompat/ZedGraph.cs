// Headless model of the ZedGraph 5.1 members the original UserControls/DiagramView (FrmDiagramView) and
// UserControls/AnalysisProgressView (FrmMonitor) use. ZedGraph draws with GDI+ (Windows-only on .NET 10) and is a
// binary package, so the pane is modelled here: curves, titles, legend, axes (linear/log, X/Y/Y2) and the axis
// auto-scaling AxisChange performs (ZedGraph Scale.PickScale with grace, zero lever, 1-2-5 major steps and whole
// log decades), which the original code reads back (e.g. to align the Y2 grid). The renderer
// (X/UI/original_forms.py) draws the pane from these values. Not modelled: label-overlap step reduction (needs the
// drawn label sizes), interactive zoom/pan (ZoomEvent) and the ZedGraph context menu (ContextMenuBuilder).
using System;
using System.Collections;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Linq;
using System.Windows.Forms;

namespace ZedGraph
{
    public enum SymbolType { Square, Diamond, Triangle, Circle, XCross, Plus, Star, TriangleDown, HDash, VDash, UserDefined, Default, None }
    public enum LegendPos { Top, Left, Right, Bottom, InsideTopLeft, InsideTopRight, InsideBotLeft, InsideBotRight, Float, TopCenter, BottomCenter, TopFlushLeft, BottomFlushLeft }
    public enum AxisType { Linear, Log, Date, Text, Ordinal, DateAsOrdinal, LinearAsOrdinal, Exponent }
    public enum FillType { None, Solid, Brush, GradientByX, GradientByY, GradientByZ, GradientByColorValue }

    public class FontSpec
    {
        public float Size { get; set; } = 12;
        public string Family { get; set; } = "Arial";
        public bool IsBold { get; set; }
        public bool IsItalic { get; set; }
        public Color FontColor { get; set; } = Color.Black;
        public Fill Fill { get; set; } = new Fill();
        public Border Border { get; } = new Border();
    }
    public class Fill
    {
        public Color Color { get; set; } = Color.White;
        public FillType Type { get; set; } = FillType.None;
        public bool IsVisible { get; set; } = true;
        public Fill() { }
        public Fill(Color color) { Color = color; Type = FillType.Solid; }
        public Fill(Color color1, Color color2, float angle) { Color = color1; Type = FillType.Brush; }
    }
    public class Border { public bool IsVisible { get; set; } = true; public Color Color { get; set; } = Color.Black; public float Width { get; set; } = 1; }
    public class Label { public string Text { get; set; } = ""; public bool IsVisible { get; set; } = true; public FontSpec FontSpec { get; set; } = new FontSpec(); }
    public class AxisLabel : Label { public bool IsOmitMag { get; set; } }
    public class Grid { public bool IsVisible { get; set; } public Color Color { get; set; } = Color.Black; public float DashOn { get; set; } = 1; public float DashOff { get; set; } = 5; public float PenWidth { get; set; } = 1; }
    public class Tic { public bool IsAllTics { get; set; } = true; public bool IsOutside { get; set; } = true; public bool IsInside { get; set; } = true; public bool IsOpposite { get; set; } = true; public float Size { get; set; } = 5; }

    public class Scale
    {
        // ZedGraph Scale.Default values.
        public const double DefaultMinGrace = 0.1, DefaultMaxGrace = 0.1, ZeroLever = 0.25, TargetXSteps = 7.0, TargetYSteps = 7.0, TargetMinorSteps = 5.0;
        double _min, _max = 1, _majorStep = 0.1, _minorStep = 0.1;
        internal Axis Owner;
        public double Min { get => _min; set { _min = value; MinAuto = false; } }
        public double Max { get => _max; set { _max = value; MaxAuto = false; } }
        public double MajorStep { get => _majorStep; set { _majorStep = value; MajorStepAuto = false; } }
        public double MinorStep { get => _minorStep; set { _minorStep = value; MinorStepAuto = false; } }
        public bool MinAuto { get; set; } = true;
        public bool MaxAuto { get; set; } = true;
        public bool MajorStepAuto { get; set; } = true;
        public bool MinorStepAuto { get; set; } = true;
        public double BaseTic { get; set; } = double.MaxValue;
        public double MinGrace { get; set; } = DefaultMinGrace;
        public double MaxGrace { get; set; } = DefaultMaxGrace;
        public bool IsVisible { get; set; } = true;
        public bool IsPreventLabelOverlap { get; set; } = true;
        public bool MagAuto { get; set; } = true;
        public int Mag { get; set; }
        public string Format { get; set; } = "g";
        public bool FormatAuto { get; set; } = true;
        public FontSpec FontSpec { get; set; } = new FontSpec();
        public bool IsLog => Owner?.Type == AxisType.Log;

        static double MyMod(double x, double y) { if (y == 0) return 0; double temp = x / y; return y * (temp - Math.Floor(temp)); }
        /// <summary>ZedGraph Scale.CalcStepSize: range/targetSteps rounded to 1, 2, 5 or 10 times a power of ten.</summary>
        public static double CalcStepSize(double range, double targetSteps)
        {
            double tempStep = range / targetSteps;
            double mag = Math.Floor(Math.Log10(tempStep));
            double magPow = Math.Pow(10.0, mag);
            double magMsd = (int)(tempStep / magPow + .5);
            if (magMsd > 5.0) magMsd = 10.0;
            else if (magMsd > 2.0) magMsd = 5.0;
            else if (magMsd > 1.0) magMsd = 2.0;
            return magMsd * magPow;
        }
        /// <summary>ZedGraph Scale.PickScale (and LinearScale/LogScale.PickScale) from the data range of the axis.</summary>
        internal void PickScale(double rangeMin, double rangeMax, bool isX)
        {
            double minVal = rangeMin, maxVal = rangeMax;
            if (double.IsInfinity(minVal) || double.IsNaN(minVal) || minVal == double.MaxValue) minVal = 0.0;
            if (double.IsInfinity(maxVal) || double.IsNaN(maxVal) || maxVal == double.MaxValue) maxVal = 0.0;
            double range = maxVal - minVal;
            if (MinAuto) { _min = minVal; if (_min < 0 || minVal - MinGrace * range >= 0.0) _min = minVal - MinGrace * range; }
            if (MaxAuto) { _max = maxVal; if (_max > 0 || maxVal + MaxGrace * range <= 0.0) _max = maxVal + MaxGrace * range; }
            if (_max == _min && MaxAuto && MinAuto)
            {
                if (Math.Abs(_max) > 1e-100) { _max *= _min < 0 ? 0.95 : 1.05; _min *= _min < 0 ? 1.05 : 0.95; }
                else { _max = 1.0; _min = -1.0; }
            }
            if (_max <= _min) { if (MaxAuto) _max = _min + 1.0; else if (MinAuto) _min = _max - 1.0; }
            if (IsLog)
            {
                if (MajorStepAuto) _majorStep = 1.0;
                Mag = 0;
                if (_min <= 0.0 && _max <= 0.0) { _min = 1.0; _max = 10.0; }
                else if (_min <= 0.0) _min = _max / 10.0;
                else if (_max <= 0.0) _max = _min * 10.0;
                if (_max - _min < 1.0e-20) { if (MaxAuto) _max *= 2.0; if (MinAuto) _min /= 2.0; }
                if (MinAuto) _min = Math.Pow(10.0, Math.Floor(Math.Log10(_min)));
                if (MaxAuto) _max = Math.Pow(10.0, Math.Ceiling(Math.Log10(_max)));
                return;
            }
            if (_max - _min < 1.0e-30)
            {
                if (MaxAuto) _max += 0.2 * (_max == 0 ? 1.0 : Math.Abs(_max));
                if (MinAuto) _min -= 0.2 * (_min == 0 ? 1.0 : Math.Abs(_min));
            }
            if (MinAuto && _min > 0 && _min / (_max - _min) < ZeroLever) _min = 0;
            if (MaxAuto && _max < 0 && Math.Abs(_max / (_max - _min)) < ZeroLever) _max = 0;
            if (MajorStepAuto) _majorStep = CalcStepSize(_max - _min, isX ? TargetXSteps : TargetYSteps);
            if (MinorStepAuto) _minorStep = CalcStepSize(_majorStep, TargetMinorSteps);
            if (MinAuto) _min -= MyMod(_min, _majorStep);
            if (MaxAuto) _max = MyMod(_max, _majorStep) == 0.0 ? _max : _max + _majorStep - MyMod(_max, _majorStep);
        }
    }
    public class Axis
    {
        protected Axis() { Scale.Owner = this; }
        public AxisLabel Title { get; } = new AxisLabel();
        public Scale Scale { get; } = new Scale();
        public AxisType Type { get; set; }
        public bool IsVisible { get; set; } = true;
        public Grid MajorGrid { get; } = new Grid();
        public Grid MinorGrid { get; } = new Grid();
        public Tic MajorTic { get; } = new Tic();
        public Tic MinorTic { get; } = new Tic();
        public Color Color { get; set; } = Color.Black;
        public double Cross { get; set; }
        public bool CrossAuto { get; set; } = true;
    }
    public class XAxis : Axis { }
    public class YAxis : Axis { }
    public class Y2Axis : Axis { public Y2Axis() { IsVisible = false; } }
    public class Legend { public LegendPos Position { get; set; } = LegendPos.Top; public bool IsVisible { get; set; } = true; public FontSpec FontSpec { get; set; } = new FontSpec(); public Fill Fill { get; set; } = new Fill(Color.White); public Border Border { get; } = new Border(); }
    public class Line { public bool IsAntiAlias { get; set; } public Color Color { get; set; } public float Width { get; set; } = 1; public bool IsVisible { get; set; } = true; public DashStyle Style { get; set; } = DashStyle.Solid; public bool IsSmooth { get; set; } }
    public class Symbol { public SymbolType Type { get; set; } public bool IsVisible { get; set; } = true; public float Size { get; set; } = 7; public Fill Fill { get; set; } = new Fill(); public Border Border { get; } = new Border(); }
    public class Chart { public Fill Fill { get; set; } = new Fill(Color.White); public Border Border { get; } = new Border(); public RectangleF Rect { get; set; } }

    public static class PointPairBase { public const double Missing = double.MaxValue; }
    public class PointPair
    {
        public const double Missing = PointPairBase.Missing;
        public double X { get; set; }
        public double Y { get; set; }
        public double Z { get; set; }
        public object Tag { get; set; }
        public PointPair() { }
        public PointPair(double x, double y) { X = x; Y = y; }
        public PointPair(double x, double y, double z) { X = x; Y = y; Z = z; }
        public PointPair(double x, double y, double z, object tag) { X = x; Y = y; Z = z; Tag = tag; }
        public PointPair(double x, double y, string label) { X = x; Y = y; Tag = label; }
        public bool IsInvalid => X == Missing || Y == Missing || double.IsInfinity(X) || double.IsInfinity(Y) || double.IsNaN(X) || double.IsNaN(Y);
    }
    public interface IPointList : ICloneable { PointPair this[int index] { get; } int Count { get; } }
    public interface IPointListEdit : IPointList { void Add(PointPair point); void Add(double x, double y); void Clear(); void RemoveAt(int index); }
    public class PointPairList : List<PointPair>, IPointListEdit
    {
        public PointPairList() { }
        public PointPairList(double[] x, double[] y) { for (int i = 0; i < Math.Min(x.Length, y.Length); i++) Add(new PointPair(x[i], y[i])); }
        public PointPairList(IPointList list) { for (int i = 0; i < list.Count; i++) Add(new PointPair(list[i].X, list[i].Y, list[i].Z)); }
        public void Add(double x, double y) => Add(new PointPair(x, y));
        public void Add(double[] x, double[] y) { for (int i = 0; i < Math.Min(x.Length, y.Length); i++) Add(x[i], y[i]); }
        public object Clone() => new PointPairList(this);
    }

    public class CurveItem
    {
        public Label Label { get; } = new Label();
        public Color Color { get; set; }
        public IPointList Points { get; set; } = new PointPairList();
        public bool IsVisible { get; set; } = true;
        public bool IsY2Axis { get; set; }
        public bool IsX2Axis { get; set; }
        public int YAxisIndex { get; set; }
        public object Tag { get; set; }
        public int NPts => Points.Count;
        // Arrays the renderer reads.
        public double[] X => Enumerable.Range(0, Points.Count).Select(i => Points[i].X).ToArray();
        public double[] Y => Enumerable.Range(0, Points.Count).Select(i => Points[i].Y).ToArray();
    }
    public class LineItem : CurveItem { public Line Line { get; } = new Line(); public Symbol Symbol { get; } = new Symbol(); }
    public class CurveList : List<CurveItem> { }

    public enum ZoomStateType { Zoom, WheelZoom, Pan, Scroll }
    /// <summary>The axis ranges of a pane at one zoom step (ZedGraph ZoomState).</summary>
    public class ZoomState
    {
        readonly (double Min, double Max, double Step, double Minor, bool MinAuto, bool MaxAuto, bool StepAuto, bool MinorAuto)[] _axes;
        public ZoomStateType Type { get; }
        public ZoomState(GraphPane pane, ZoomStateType type) { Type = type; _axes = Array.ConvertAll(pane.Axes, a => (a.Scale.Min, a.Scale.Max, a.Scale.MajorStep, a.Scale.MinorStep, a.Scale.MinAuto, a.Scale.MaxAuto, a.Scale.MajorStepAuto, a.Scale.MinorStepAuto)); }
        public void ApplyState(GraphPane pane)
        {
            Axis[] axes = pane.Axes;
            for (int i = 0; i < axes.Length && i < _axes.Length; i++)
            {
                Scale s = axes[i].Scale;
                s.Min = _axes[i].Min; s.Max = _axes[i].Max; s.MajorStep = _axes[i].Step; s.MinorStep = _axes[i].Minor;
                s.MinAuto = _axes[i].MinAuto; s.MaxAuto = _axes[i].MaxAuto; s.MajorStepAuto = _axes[i].StepAuto; s.MinorStepAuto = _axes[i].MinorAuto;
            }
        }
    }
    public class ZoomStateStack : List<ZoomState>
    {
        public bool IsEmpty => Count == 0;
        public ZoomState Top => IsEmpty ? null : this[Count - 1];
        public ZoomState Push(GraphPane pane, ZoomStateType type) { var s = new ZoomState(pane, type); Add(s); return s; }
        public ZoomState Pop(GraphPane pane) { if (IsEmpty) return null; ZoomState s = this[Count - 1]; RemoveAt(Count - 1); s.ApplyState(pane); return s; }
    }

    public class GraphPane
    {
        public CurveList CurveList { get; } = new CurveList();
        public Label Title { get; } = new Label();
        public Legend Legend { get; } = new Legend();
        public XAxis XAxis { get; } = new XAxis();
        public YAxis YAxis { get; } = new YAxis();
        public Y2Axis Y2Axis { get; } = new Y2Axis();
        public Fill Fill { get; set; } = new Fill(Color.White);
        public Chart Chart { get; } = new Chart();
        public Border Border { get; } = new Border();
        public bool IsFontsScaled { get; set; } = true;
        public bool IsPenWidthScaled { get; set; }
        public bool IsIgnoreMissing { get; set; }
        public ZoomStateStack ZoomStack { get; } = new ZoomStateStack();
        internal Axis[] Axes => new Axis[] { XAxis, YAxis, Y2Axis };

        public LineItem AddCurve(string label, double[] x, double[] y, Color color, SymbolType symbolType) => AddCurve(label, new PointPairList(x, y), color, symbolType);
        public LineItem AddCurve(string label, double[] x, double[] y, Color color) => AddCurve(label, new PointPairList(x, y), color, SymbolType.Default);
        public LineItem AddCurve(string label, IPointList points, Color color) => AddCurve(label, points, color, SymbolType.Default);
        public LineItem AddCurve(string label, IPointList points, Color color, SymbolType symbolType)
        {
            var curve = new LineItem { Color = color, Points = points ?? new PointPairList() };
            curve.Label.Text = label;
            curve.Line.Color = color;
            curve.Symbol.Type = symbolType;
            curve.Symbol.Border.Color = color;
            CurveList.Add(curve);
            return curve;
        }
        /// <summary>ZedGraph GraphPane.AxisChange: the data range of the visible curves of each axis (log axes skip
        /// non-positive values, missing points are skipped), then each axis picks its scale.</summary>
        public void AxisChange()
        {
            (double Min, double Max) Range(Func<CurveItem, bool> onAxis, bool useX, bool log)
            {
                double min = double.MaxValue, max = double.MinValue;
                foreach (CurveItem curve in CurveList)
                {
                    if (!curve.IsVisible || !onAxis(curve)) continue;
                    for (int i = 0; i < curve.Points.Count; i++)
                    {
                        PointPair p = curve.Points[i];
                        if (p.IsInvalid) continue;
                        double v = useX ? p.X : p.Y;
                        if (log && v <= 0) continue;
                        if (v < min) min = v;
                        if (v > max) max = v;
                    }
                }
                return min == double.MaxValue ? (double.MaxValue, double.MaxValue) : (min, max);
            }
            var x = Range(c => true, true, XAxis.Type == AxisType.Log);
            var y = Range(c => !c.IsY2Axis, false, YAxis.Type == AxisType.Log);
            var y2 = Range(c => c.IsY2Axis, false, Y2Axis.Type == AxisType.Log);
            XAxis.Scale.PickScale(x.Min, x.Max, true);
            YAxis.Scale.PickScale(y.Min, y.Max, false);
            Y2Axis.Scale.PickScale(y2.Min, y2.Max, false);
        }
    }

    public class ZedGraphControl : Control
    {
        public GraphPane GraphPane { get; set; } = new GraphPane();
        public double ScrollGrace { get; set; }
        public double ScrollMaxX { get; set; }
        public double ScrollMaxY { get; set; }
        public double ScrollMaxY2 { get; set; }
        public double ScrollMinX { get; set; }
        public double ScrollMinY { get; set; }
        public double ScrollMinY2 { get; set; }
        public bool UseExtendedPrintDialog { get; set; }
        public bool IsShowPointValues { get; set; }
        public bool IsShowContextMenu { get; set; } = true;
        public bool IsEnableZoom { get; set; } = true;
        public bool IsEnableHZoom { get; set; } = true;
        public bool IsEnableVZoom { get; set; } = true;
        public bool IsEnableWheelZoom { get; set; } = true;
        public bool IsAntiAlias { get; set; }
        public string PointValueFormat { get; set; } = "G";
        public enum ContextMenuObjectState { InactiveSelection, ActiveSelection, Background }
        public delegate void ZoomEventHandler(ZedGraphControl sender, ZoomState oldState, ZoomState newState);
        public delegate void ContextMenuBuilderEventHandler(ZedGraphControl sender, ContextMenuStrip menuStrip, Point mousePt, ContextMenuObjectState objState);
        public delegate string PointValueHandler(ZedGraphControl sender, GraphPane pane, CurveItem curve, int iPt);
        public event ZoomEventHandler ZoomEvent;
        public event ContextMenuBuilderEventHandler ContextMenuBuilder;
        public event PointValueHandler PointValueEvent;
        /// <summary>Recomputes the axis ranges from the curves (GraphPane.AxisChange) and redraws.</summary>
        public void AxisChange() { GraphPane.AxisChange(); Notify("Graph"); }
        /// <summary>ZedGraph RestoreScale: pushes the current scales on the zoom stack, resets every axis to auto
        /// scale (Axis.ResetAutoScale + AxisChange) and raises ZoomEvent.</summary>
        public void RestoreScale(GraphPane pane)
        {
            if (pane == null) return;
            var oldState = new ZoomState(pane, ZoomStateType.Zoom);
            pane.ZoomStack.Push(pane, ZoomStateType.Zoom);
            foreach (Axis axis in pane.Axes)
            {
                Scale s = axis.Scale;
                s.MinAuto = s.MaxAuto = s.MajorStepAuto = s.MinorStepAuto = s.MagAuto = s.FormatAuto = true;
                axis.CrossAuto = true;
            }
            pane.AxisChange();
            ZoomEvent?.Invoke(this, oldState, new ZoomState(pane, ZoomStateType.Zoom));
            Notify("Graph");
        }
        /// <summary>ZedGraph ZoomOut: pops the last zoom state (applying it) and raises ZoomEvent.</summary>
        public void ZoomOut(GraphPane pane)
        {
            if (pane == null || pane.ZoomStack.IsEmpty) return;
            ZoomStateType type = pane.ZoomStack[pane.ZoomStack.Count - 1].Type;
            var oldState = new ZoomState(pane, type);
            ZoomState newState = pane.ZoomStack.Pop(pane);
            ZoomEvent?.Invoke(this, oldState, newState);
            Notify("Graph");
        }
        /// <summary>Point tooltip text: PointValueEvent, else "label: x, y" (ZedGraph's default).</summary>
        public string PointValueText(CurveItem curve, int index)
        {
            if (PointValueEvent != null) return PointValueEvent(this, GraphPane, curve, index);
            PointPair p = curve.Points[index];
            return curve.Label.Text + ": " + p.X.ToString(PointValueFormat) + ", " + p.Y.ToString(PointValueFormat);
        }
    }
}
