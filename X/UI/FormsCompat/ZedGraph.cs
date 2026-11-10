// Headless model of the ZedGraph members the original UserControls/DiagramView (FrmDiagramView) uses. ZedGraph
// draws with GDI+ (Windows-only on .NET 10); here the pane keeps the curves, titles, legend and axis limits the
// original code sets, and the renderer (X/UI/original_forms.py) draws them.
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;

namespace ZedGraph
{
    public enum SymbolType { Square, Diamond, Triangle, Circle, XCross, Plus, Star, TriangleDown, HDash, VDash, UserDefined, Default, None }
    public enum LegendPos { Top, Left, Right, Bottom, InsideTopLeft, InsideTopRight, InsideBotLeft, InsideBotRight, Float, TopCenter, BottomCenter, TopFlushLeft, BottomFlushLeft }

    public class Label { public string Text { get; set; } = ""; public bool IsVisible { get; set; } = true; }
    public class Scale
    {
        double _min, _max;
        public double Min { get => _min; set { _min = value; MinAuto = false; } }
        public double Max { get => _max; set { _max = value; MaxAuto = false; } }
        public bool MinAuto { get; set; } = true;
        public bool MaxAuto { get; set; } = true;
    }
    public class Axis { public Label Title { get; } = new Label(); public Scale Scale { get; } = new Scale(); public bool IsVisible { get; set; } = true; }
    public class XAxis : Axis { }
    public class YAxis : Axis { }
    public class Legend { public LegendPos Position { get; set; } = LegendPos.Top; public bool IsVisible { get; set; } = true; }
    public class Line { public bool IsAntiAlias { get; set; } public Color Color { get; set; } public float Width { get; set; } = 1; public bool IsVisible { get; set; } = true; }
    public class Symbol { public SymbolType Type { get; set; } public bool IsVisible { get; set; } = true; public float Size { get; set; } = 7; }
    public class CurveItem
    {
        public Label Label { get; } = new Label();
        public Color Color { get; set; }
        public double[] X { get; set; } = new double[0];
        public double[] Y { get; set; } = new double[0];
        public bool IsVisible { get; set; } = true;
    }
    public class LineItem : CurveItem { public Line Line { get; } = new Line(); public Symbol Symbol { get; } = new Symbol(); }
    public class CurveList : List<CurveItem> { }

    public class GraphPane
    {
        public CurveList CurveList { get; } = new CurveList();
        public Label Title { get; } = new Label();
        public Legend Legend { get; } = new Legend();
        public XAxis XAxis { get; } = new XAxis();
        public YAxis YAxis { get; } = new YAxis();
        public LineItem AddCurve(string label, double[] x, double[] y, Color color, SymbolType symbolType)
        {
            var curve = new LineItem { Color = color, X = (double[])x.Clone(), Y = (double[])y.Clone() };
            curve.Label.Text = label;
            curve.Line.Color = color;
            curve.Symbol.Type = symbolType;
            CurveList.Add(curve);
            return curve;
        }
    }

    public class ZedGraphControl : Control
    {
        public GraphPane GraphPane { get; } = new GraphPane();
        public double ScrollGrace { get; set; }
        public double ScrollMaxX { get; set; }
        public double ScrollMaxY { get; set; }
        public double ScrollMaxY2 { get; set; }
        public double ScrollMinX { get; set; }
        public double ScrollMinY { get; set; }
        public double ScrollMinY2 { get; set; }
        public bool UseExtendedPrintDialog { get; set; }
        public bool IsShowPointValues { get; set; }
        /// <summary>ZedGraph recomputes the axis ranges from the curves; the renderer draws from the pane.</summary>
        public void AxisChange() => Notify("Graph");
        public void RestoreScale(GraphPane pane) => Notify("Graph");
        public void ZoomOut(GraphPane pane) => Notify("Graph");
    }
}
