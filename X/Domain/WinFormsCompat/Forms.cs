// Same names/values as System.Windows.Forms so original code and persisted
// enum values keep their meaning.
using System;

namespace System.Windows.Forms
{
    public enum DialogResult { None = 0, OK = 1, Cancel = 2, Abort = 3, Retry = 4, Ignore = 5, Yes = 6, No = 7, TryAgain = 10, Continue = 11 }

    public enum MessageBoxButtons { OK = 0, OKCancel = 1, AbortRetryIgnore = 2, YesNoCancel = 3, YesNo = 4, RetryCancel = 5, CancelTryContinue = 6 }

    public enum MessageBoxIcon { None = 0, Hand = 16, Stop = 16, Error = 16, Question = 32, Exclamation = 48, Warning = 48, Asterisk = 64, Information = 64 }

    public enum MessageBoxDefaultButton { Button1 = 0, Button2 = 256, Button3 = 512, Button4 = 768 }

    public interface IWin32Window
    {
        IntPtr Handle { get; }
    }
}

namespace System.Windows.Forms
{
    /// <summary>Only the message-pump hook used by original domain code. The
    /// cross-platform UI may set <see cref="DoEventsHandler"/>; without a UI it
    /// does nothing.</summary>
    public static class Application
    {
        public static Action DoEventsHandler;
        public static string StartupPath => AppContext.BaseDirectory.TrimEnd(System.IO.Path.DirectorySeparatorChar);
        public static string ProductVersion => System.Reflection.Assembly.GetEntryAssembly()?.GetName().Version?.ToString() ?? "3.0.0.0";
        public static bool MessageLoop => DoEventsHandler != null;
        public static void DoEvents() => DoEventsHandler?.Invoke();
    }
}
namespace System.Windows.Forms
{
    public enum FormWindowState { Normal, Minimized, Maximized }
    [Flags] public enum Keys { None=0, Shift=65536, Control=131072, Alt=262144 }
    [Flags] public enum MouseButtons { None=0, Left=1048576, Right=2097152, Middle=4194304 }
    public class MouseEventArgs : EventArgs
    {
        public MouseButtons Button {get;}
        public int Clicks {get;}
        public int X {get;}
        public int Y {get;}
        public int Delta {get;}
        public MouseEventArgs(MouseButtons button,int clicks,int x,int y,int delta) {Button=button;Clicks=clicks;X=x;Y=y;Delta=delta;}
    }
}
