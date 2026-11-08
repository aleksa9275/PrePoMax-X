// Nonvisual editor metadata. The Qt property host dispatches the editor types;
// model values and conversion remain in the original property views.
using System.Drawing.Design;
namespace UserControls
{
    public class ColorEditorEx : UITypeEditor { }
    public class FlagsEnumEditorUIEditor : UITypeEditor { }
    public class DampingRatiosAndValuesUIEditor : UITypeEditor { }
}
