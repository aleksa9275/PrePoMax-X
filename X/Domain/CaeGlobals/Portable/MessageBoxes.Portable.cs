// PrePoMax-X portable counterpart of CaeGlobals/MessageBoxes.WinForms.cs (D062).
// The original unattended/automation behaviour in MessageBoxes.cs is shared
// unchanged; only the native dialog and UI-thread hop are supplied by the host.
using System;
using System.Windows.Forms;

namespace CaeGlobals
{
    public static partial class MessageBoxes
    {
        /// <summary>Shows a dialog on the cross-platform UI and returns the user's answer.
        /// When no UI has registered, interactive prompts are answered as in
        /// <see cref="MessageBoxModeEnum.Strict"/> mode: reports go to the output and
        /// decisions are refused, because no user is present.</summary>
        public static Func<IWin32Window, string, string, MessageBoxButtons, MessageBoxIcon, DialogResult> InteractivePresenter;
        /// <summary>Runs a function on the UI thread (the original Form.Invoke hop); null runs it directly.</summary>
        public static Func<Func<object>, object> UiDispatcher;

        private static DialogResult ShowInteractive(string text, string caption, MessageBoxButtons buttons,
                                                    MessageBoxIcon icon)
        {
            return ShowNative(null, text, caption, buttons, icon);
        }
        private static DialogResult ShowNative(IWin32Window owner, string text, string caption, MessageBoxButtons buttons,
                                               MessageBoxIcon icon)
        {
            var presenter = InteractivePresenter;
            if (presenter == null) return ShowCrossThread(text, caption, buttons, icon, MessageBoxModeEnum.Strict);
            System.Threading.Interlocked.Increment(ref _numberOfOpenMessageBoxes);
            try
            {
                return presenter(owner, text, caption, buttons, icon);
            }
            finally
            {
                System.Threading.Interlocked.Decrement(ref _numberOfOpenMessageBoxes);
            }
        }
        private static object InvokeIfRequired(Func<object> function)
        {
            var dispatcher = UiDispatcher;
            return dispatcher != null ? dispatcher(function) : function();
        }
    }
}
