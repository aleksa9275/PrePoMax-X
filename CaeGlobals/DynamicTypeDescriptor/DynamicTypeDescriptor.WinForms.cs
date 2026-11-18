// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://github.com/PrePoMax/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

// PrePoMax-X: WinForms-only editor, moved verbatim from DynamicTypeDescriptor.cs
// so the portable domain build compiles without WinForms (D062). Included only
// by the original project; the portable build supplies X/Domain/CaeGlobals/Portable.

using System;
using System.Drawing.Design;
using System.Windows.Forms.Design;

namespace DynamicTypeDescriptor
{
    public class StandardValueEditor : UITypeEditor
    {
        private StandardValueEditorUI m_ui = new StandardValueEditorUI();

        public StandardValueEditor()
        {

        }

        public override bool GetPaintValueSupported(System.ComponentModel.ITypeDescriptorContext context)
        {
            return false;
        }

        public override UITypeEditorEditStyle GetEditStyle(System.ComponentModel.ITypeDescriptorContext context)
        {
            return UITypeEditorEditStyle.DropDown;
        }

        public override bool IsDropDownResizable
        {
            get
            {
                return true;
            }
        }

        public override object EditValue(System.ComponentModel.ITypeDescriptorContext context, IServiceProvider provider, object value)
        {
            if (provider != null)
            {
                IWindowsFormsEditorService editorService = provider.GetService(typeof(IWindowsFormsEditorService)) as IWindowsFormsEditorService;
                if (editorService == null)
                    return value;

                m_ui.SetData(context, editorService, value);

                editorService.DropDownControl(m_ui);

                value = m_ui.GetValue();

            }

            return value;
        }
    }
}
