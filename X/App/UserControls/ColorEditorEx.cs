// UserControls/ProperyGrid/ColorEditorEx.cs extends the WinForms ColorEditor through its private ColorUI class
// (reflection on System.Design internals). The property grid of the renderer recognizes the editor by this type
// and edits the colour itself, as for the workbench (X/Domain/UserControls/EditorMetadata.cs).
using System.Drawing.Design;
namespace UserControls
{
    public class ColorEditorEx : UITypeEditor { }
}
