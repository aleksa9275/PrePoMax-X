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
        public static void DoEvents() => DoEventsHandler?.Invoke();
    }
}
