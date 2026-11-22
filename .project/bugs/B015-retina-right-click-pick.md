# B015 — a right click on a part picked in control units on a Retina display (fixed)

22 November 2026; found in M3-1b when the app probe ran on Linux, where the display scale is 1. There, a right click
in the middle of the view hit the part and opened the part's menu. On a Retina Mac (scale 2) the same click had
opened the view's menu.

**Cause.** `vtkControl.NativeWidgets.cs` turns the native right-press position into control units for the
`MouseEventArgs` of `style_RightButtonPressEvent`, because the menus are placed in control units (D066). The
original handler then passed that position to `NativeMirrorPickPoint`. The native pick takes device pixels, as its
three other callers pass them. On Retina the pick therefore looked at half the coordinates, towards the lower left.
A part under the mouse was missed, the view's menu opened instead of the part's, and a part elsewhere could be
picked by mistake.

**Fix.** `vtkControl.cs` converts the position with `VtkNativeView.ToDevice` for the pick only. The menu position
stays in control units. Windows is unchanged, since its scale is 1. The app probe now right-clicks empty space
(view menu, where clicked) and a part found by the native pick (part menu, where clicked). On macOS the old
`vtkControl.dll` fails that check (menu at 0,0) and the fixed one passes it. Linux passes it too.

The published macOS preview 2 (`release/macos-arm64-preview`, source `e076f692`) still has the bug.
