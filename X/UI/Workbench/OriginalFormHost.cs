// Main-window side of the original form hosting (OriginalFormHost.g.cs holds the FrmMain members verbatim).
// The host stands in for FrmMain as the forms' owner window. FrmMain members that belong to its menus,
// tree, viewport, state machine and renderer are forwarded to the toolkit workbench through the hooks below.
using System.Windows.Forms;
using PrePoMax.Forms;

namespace PrePoMax;

public sealed partial class OriginalFormHost : Form
{
    readonly Controller _controller;
    public OriginalFormHost(Controller controller)
    {
        _controller = controller;
        Text = "PrePoMax";
        CreateForms();
    }
    public Controller Controller => _controller;
    public IReadOnlyList<Form> AllForms => _allForms;
    public FrmSelectItemSet SelectItemSetForm => _frmSelectItemSet;
    /// <summary>The visible item form, if any (FrmMain shows one at a time; FrmSelectItemSet accompanies it).</summary>
    public Form ActiveItemForm => _allForms.FirstOrDefault(f => f.Visible && f is not FrmSelectItemSet);

    // FrmMain.SetStateWorking/SetStateReady: false when another task is running.
    public Func<string, bool, bool> StateWorkingHandler { get; set; }
    public Action<string> StateReadyHandler { get; set; }
    // FrmMain.SetMenuAndToolStripVisibilityByItemForm / ByAnimation.
    public Action<bool> MenusActiveHandler { get; set; }
    public Action<bool> AnimationMenusHandler { get; set; }
    // FrmMain.UpdateHighlightFromTree (model tree highlight) and CommitViewportEdit (viewport text editor).
    public Action HighlightFromTreeHandler { get; set; }
    public Func<bool> CommitViewportEditHandler { get; set; }
    // FrmMain.CaptureViewport (renderer screenshot).
    public Func<CaptureViewportProperties, bool> CaptureViewportHandler { get; set; }

    // FrmMain status label state: Globals.ReadyText or the text of the running state.
    readonly ToolStripStatusLabel tsslState = new ToolStripStatusLabel { Text = Globals.ReadyText };
    public string State => tsslState.Text;
    /// <summary>FrmMain.SetStateWorking: only from the ready state.</summary>
    public bool SetStateWorking(string text, bool showCancelButton = false)
    {
        if (tsslState.Text != Globals.ReadyText) return false;
        if (StateWorkingHandler != null && !StateWorkingHandler(text, showCancelButton)) return false;
        tsslState.Text = text;
        return true;
    }
    /// <summary>FrmMain.SetStateReady: ends the state started with the same text.</summary>
    public void SetStateReady(string currentText)
    {
        if (tsslState.Text != currentText) return;
        tsslState.Text = Globals.ReadyText;
        StateReadyHandler?.Invoke(currentText);
    }
    // FrmMain.WriteDataToOutput (output panel).
    public Action<string> OutputHandler { get; set; }
    void WriteDataToOutput(string data) => OutputHandler?.Invoke(data);
    /// <summary>FrmMain.New with undefined properties: the modal FrmNewModel, then a new model.</summary>
    public bool SelectNewModel(bool cancelPossible) => SelectNewModelProperties(cancelPossible);
    public void ApplyNewModelProperties() => SetNewModelProperties();
    void SetMenuAndToolStripVisibilityByItemForm(bool menusActive) => MenusActiveHandler?.Invoke(menusActive);
    void SetMenuAndToolStripVisibilityByAnimation(bool menusActive) => AnimationMenusHandler?.Invoke(menusActive);
    void UpdateHighlightFromTree() => HighlightFromTreeHandler?.Invoke();
    bool CommitViewportEdit() => CommitViewportEditHandler?.Invoke() ?? false;
    bool CaptureViewport(CaptureViewportProperties properties) => CaptureViewportHandler?.Invoke(properties) ?? false;
    void InvokeIfRequired(Action action) => action();

    /// <summary>Calls a FrmMain create/edit entry point by its original name (menu and tree dispatch).</summary>
    public void Invoke(string method, params object[] arguments)
    {
        var candidates = GetType().GetMethods(System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public)
            .Where(m => m.Name == method && m.GetParameters().Length == arguments.Length).ToArray();
        if (candidates.Length != 1) throw new MissingMethodException(nameof(OriginalFormHost), method);
        try { candidates[0].Invoke(this, arguments); }
        catch (System.Reflection.TargetInvocationException e) when (e.InnerException != null) { System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(e.InnerException).Throw(); }
    }
    /// <summary>Calls a FrmMain entry point filling its original parameters by name: sender/e (menu click),
    /// stepName, partNames, operation (surface operations) and the edited item name.</summary>
    public void InvokeEntry(string method, string step, string name, string[] partNames, string operation)
    {
        var candidates = GetType().GetMethods(System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public)
            .Where(m => m.Name == method).ToArray();
        if (candidates.Length != 1) throw new MissingMethodException(nameof(OriginalFormHost), method);
        var arguments = candidates[0].GetParameters().Select(p => p.Name switch
        {
            "sender" => (object)null,
            "e" => EventArgs.Empty,
            "stepName" => step,
            "partNames" => partNames ?? Array.Empty<string>(),
            "operation" => Enum.Parse(p.ParameterType, operation),
            _ when p.ParameterType == typeof(string) => name,
            _ => throw new NotSupportedException(method + ": parameter " + p.Name),
        }).ToArray();
        try { candidates[0].Invoke(this, arguments); }
        catch (System.Reflection.TargetInvocationException e) when (e.InnerException != null) { System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(e.InnerException).Throw(); }
    }
    public string[] EntryPoints => GetType().GetMethods(System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.DeclaredOnly)
        .Select(m => m.Name).Distinct().OrderBy(n => n).ToArray();
}
