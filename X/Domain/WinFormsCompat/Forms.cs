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
    [Flags] public enum Keys { KeyCode=65535, Modifiers=-65536, None=0, LButton=1, RButton=2, Cancel=3, MButton=4, XButton1=5, XButton2=6, Back=8, Tab=9, LineFeed=10, Clear=12, Return=13, Enter=13, ShiftKey=16, ControlKey=17, Menu=18, Pause=19, Capital=20, CapsLock=20, Escape=27, Space=32, Prior=33, PageUp=33, Next=34, PageDown=34, End=35, Home=36, Left=37, Up=38, Right=39, Down=40, Select=41, Print=42, Execute=43, Snapshot=44, PrintScreen=44, Insert=45, Delete=46, Help=47, D0=48, D1=49, D2=50, D3=51, D4=52, D5=53, D6=54, D7=55, D8=56, D9=57, A=65, B=66, C=67, D=68, E=69, F=70, G=71, H=72, I=73, J=74, K=75, L=76, M=77, N=78, O=79, P=80, Q=81, R=82, S=83, T=84, U=85, V=86, W=87, X=88, Y=89, Z=90, LWin=91, RWin=92, Apps=93, Sleep=95, NumPad0=96, NumPad1=97, NumPad2=98, NumPad3=99, NumPad4=100, NumPad5=101, NumPad6=102, NumPad7=103, NumPad8=104, NumPad9=105, Multiply=106, Add=107, Separator=108, Subtract=109, Decimal=110, Divide=111, F1=112, F2=113, F3=114, F4=115, F5=116, F6=117, F7=118, F8=119, F9=120, F10=121, F11=122, F12=123, NumLock=144, Scroll=145, LShiftKey=160, RShiftKey=161, LControlKey=162, RControlKey=163, LMenu=164, RMenu=165, OemSemicolon=186, Oem1=186, Oemplus=187, Oemcomma=188, OemMinus=189, OemPeriod=190, OemQuestion=191, Oem2=191, Oemtilde=192, Oem3=192, OemOpenBrackets=219, Oem4=219, OemPipe=220, Oem5=220, OemCloseBrackets=221, Oem6=221, OemQuotes=222, Oem7=222, Shift=65536, Control=131072, Alt=262144 }
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
namespace System.Windows.Forms { public delegate void MethodInvoker(); }
namespace System.Windows.Forms.Design { public sealed class FolderNameEditor : System.Drawing.Design.UITypeEditor {} }
namespace System.Windows.Forms.Design { public sealed class FileNameEditor : System.Drawing.Design.UITypeEditor {} }
