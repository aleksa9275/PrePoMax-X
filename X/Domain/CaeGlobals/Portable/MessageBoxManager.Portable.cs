// PrePoMax-X portable counterpart of CaeGlobals/MessageBoxManager.cs (D062). The original renames the buttons of
// the native Win32 message boxes of a thread through a user32 window hook (WH_CALLWNDPROCRET). The cross-platform
// message box presenter labels its buttons with these texts while the manager is registered; the public members and
// their defaults are the original's.
namespace System.Windows.Forms
{
    public class MessageBoxManager
    {
        public static string OK = "&OK";
        public static string Cancel = "&Cancel";
        public static string Abort = "&Abort";
        public static string Retry = "&Retry";
        public static string Ignore = "&Ignore";
        public static string Yes = "&Yes";
        public static string No = "&No";
        [ThreadStatic] static bool registered;
        /// <summary>True on a thread that registered: its message boxes use the texts above.</summary>
        public static bool IsRegistered => registered;
        public static void Register()
        {
            if (registered) throw new NotSupportedException("One hook per thread allowed.");
            registered = true;
        }
        public static void Unregister() => registered = false;
    }
}
