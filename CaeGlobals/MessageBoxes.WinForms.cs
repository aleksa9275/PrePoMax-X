// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://github.com/PrePoMax/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

// PrePoMax-X: WinForms-only members, moved verbatim from MessageBoxes.cs so the
// portable domain build compiles without WinForms (D062). Included only by the
// original project; the portable build supplies X/Domain/CaeGlobals/Portable.

using System;
using System.Windows.Forms;

namespace CaeGlobals
{
    public static partial class MessageBoxes
    {
        public static Form ParentForm;
        private static DialogResult ShowInteractive(string text, string caption, MessageBoxButtons buttons,
                                                    MessageBoxIcon icon)
        {
            using (new CenterWinDialog(ParentForm))
            {
                return ShowNative(ParentForm, text, caption, buttons, icon);
            }
        }
        private static DialogResult ShowNative(IWin32Window owner, string text, string caption, MessageBoxButtons buttons,
                                               MessageBoxIcon icon)
        {
            System.Threading.Interlocked.Increment(ref _numberOfOpenMessageBoxes);
            try
            {
                return MessageBox.Show(owner, text, caption, buttons, icon);
            }
            finally
            {
                System.Threading.Interlocked.Decrement(ref _numberOfOpenMessageBoxes);
            }
        }
        private static object InvokeIfRequired(Func<object> function)
        {
            if (ParentForm.InvokeRequired)
            {
                return (object)ParentForm.Invoke((MethodInvoker)delegate () { function(); });
            }
            else
            {
                return function();
            }
        }
    }
}
