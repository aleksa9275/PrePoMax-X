using ZedGraph;
namespace UserControls { public partial class XYPlotSettings {
        public LegendPos GetLegendPos()
        {
            switch (_legendPosition)
            {
                case XYPlotLegendPositionEnum.Top: return LegendPos.Top;
                case XYPlotLegendPositionEnum.TopFlushLeft: return LegendPos.TopFlushLeft;
                case XYPlotLegendPositionEnum.BottomCenter: return LegendPos.BottomCenter;
                case XYPlotLegendPositionEnum.Bottom: return LegendPos.Bottom;
                case XYPlotLegendPositionEnum.BottomFlushLeft: return LegendPos.BottomFlushLeft;
                case XYPlotLegendPositionEnum.Left: return LegendPos.Left;
                case XYPlotLegendPositionEnum.Right: return LegendPos.Right;
                case XYPlotLegendPositionEnum.InsideTopLeft: return LegendPos.InsideTopLeft;
                case XYPlotLegendPositionEnum.InsideTopRight: return LegendPos.InsideTopRight;
                case XYPlotLegendPositionEnum.InsideBotLeft: return LegendPos.InsideBotLeft;
                case XYPlotLegendPositionEnum.InsideBotRight: return LegendPos.InsideBotRight;
                default: return LegendPos.TopCenter;
            }
        }
        public void SetLegendPos(LegendPos legendPos)
        {
            switch (legendPos)
            {
                case LegendPos.Top: _legendPosition = XYPlotLegendPositionEnum.Top; break;
                case LegendPos.TopFlushLeft: _legendPosition = XYPlotLegendPositionEnum.TopFlushLeft; break;
                case LegendPos.BottomCenter: _legendPosition = XYPlotLegendPositionEnum.BottomCenter; break;
                case LegendPos.Bottom: _legendPosition = XYPlotLegendPositionEnum.Bottom; break;
                case LegendPos.BottomFlushLeft: _legendPosition = XYPlotLegendPositionEnum.BottomFlushLeft; break;
                case LegendPos.Left: _legendPosition = XYPlotLegendPositionEnum.Left; break;
                case LegendPos.Right: _legendPosition = XYPlotLegendPositionEnum.Right; break;
                case LegendPos.InsideTopLeft: _legendPosition = XYPlotLegendPositionEnum.InsideTopLeft; break;
                case LegendPos.InsideTopRight: _legendPosition = XYPlotLegendPositionEnum.InsideTopRight; break;
                case LegendPos.InsideBotLeft: _legendPosition = XYPlotLegendPositionEnum.InsideBotLeft; break;
                case LegendPos.InsideBotRight: _legendPosition = XYPlotLegendPositionEnum.InsideBotRight; break;
                default: _legendPosition = XYPlotLegendPositionEnum.TopCenter; break;
            }
        }
}}
