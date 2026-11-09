using CaeGlobals;using PrePoMax;using UserControls;using CaeResults;
namespace PrePoMaxX.UI;
public sealed partial class PlotSession(Controller controller)
{
    readonly Controller _controller=controller;
    public XYPlotPanelState State {get;set;}=new();
    public sealed class XYPlot(XYPlotState state,int limit)
    {
        public bool AddCurve(string name,double[] x,double[] y){if(state.Curves.Count>=limit)return false;
        var colors=new[]{System.Drawing.Color.FromArgb(31,119,180),System.Drawing.Color.FromArgb(214,39,40),System.Drawing.Color.FromArgb(44,160,44),System.Drawing.Color.FromArgb(255,127,14),System.Drawing.Color.FromArgb(148,103,189),System.Drawing.Color.FromArgb(23,190,207),System.Drawing.Color.FromArgb(140,86,75),System.Drawing.Color.FromArgb(227,119,194)};
        state.Curves.Add(new XYPlotCurveState{XValues=x,YValues=y,Settings=new XYPlotCurveSettings{Name=name,Color=colors[state.Curves.Count%colors.Length],LineWidth=2}});return true;}
    }
    public int AddPlot(){if(State.Plots.Count>=4)throw new CaeException("The maximum number of XY plots is 4.");State.Plots.Add(new());State.SelectedPlotIndex=State.Plots.Count-1;return State.SelectedPlotIndex;}
    XYPlot Plot(int index)=>new(State.Plots[index],controller.Settings.Post.MaxCurvesPerPlot);
    public bool AddHistory(int index,HistoryResultData source)=>AddHistoryOutputToPlot(source,Plot(index));
    public bool AddAmplitude(int index,string name)=>AddAmplitudeToPlot(controller.GetAmplitude(name),Plot(index));
    public PropertySheet Properties(int index)=>new(State.Plots[index].Settings);
    public PropertySheet CurveProperties(int index,int curve)=>new(State.Plots[index].Curves[curve].Settings);
    public void RemovePlot(int index){State.Plots.RemoveAt(index);State.SelectedPlotIndex=Math.Clamp(State.SelectedPlotIndex,0,Math.Max(0,State.Plots.Count-1));}
    public void RemoveCurve(int index,int curve)=>State.Plots[index].Curves.RemoveAt(curve);
}
