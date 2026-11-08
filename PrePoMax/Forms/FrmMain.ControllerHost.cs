namespace PrePoMax
{
    // The original WinForms main window implements the same presentation boundary
    // as the native/headless host; the engineering Controller depends on it only.
    public partial class FrmMain : IControllerHost { }
}
