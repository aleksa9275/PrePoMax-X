// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://github.com/PrePoMax/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

// PrePoMax-X: WinForms-only members, moved verbatim from Extensions.cs so the portable
// domain build compiles without WinForms (D062). Included only by the original project.
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;

namespace CaeGlobals
{
    public static partial class ExtensionMethods
    {
        // Property grid items
        public static IEnumerable<GridItem> EnumerateAllItems(this PropertyGrid grid)
        {
            if (grid == null) yield break;
            // Get to root item
            GridItem start = grid.SelectedGridItem;
            while (start.Parent != null)
            {
                start = start.Parent;
            }
            //
            foreach (GridItem item in start.EnumerateAllItems())
            {
                yield return item;
            }
        }
        public static IEnumerable<GridItem> EnumerateAllItems(this GridItem item)
        {
            if (item == null) yield break;
            //
            yield return item;
            foreach (GridItem child in item.GridItems)
            {
                foreach (GridItem gc in child.EnumerateAllItems())
                {
                    yield return gc;
                }
            }
        }
        // Controls
        public static void SetDoubleBuffered(System.Windows.Forms.Control c)
        {
            //Taxes: Remote Desktop Connection and painting
            //http://blogs.msdn.com/oldnewthing/archive/2006/01/03/508694.aspx
            if (System.Windows.Forms.SystemInformation.TerminalServerSession)
                return;

            System.Reflection.PropertyInfo aProp =
                  typeof(System.Windows.Forms.Control).GetProperty(
                        "DoubleBuffered",
                        System.Reflection.BindingFlags.NonPublic |
                        System.Reflection.BindingFlags.Instance);

            aProp.SetValue(c, true, null);
        }
        public static void SetLocationInsideWorkingArea(this Form form, Point location)
        {
            Rectangle workingArea = Screen.FromPoint(location).WorkingArea;
            Size size = new Size(Math.Min(form.Width, workingArea.Width), Math.Min(form.Height, workingArea.Height));
            //
            if (size != form.Size)
            {
                form.MinimumSize = new Size(Math.Min(form.MinimumSize.Width, size.Width),
                                            Math.Min(form.MinimumSize.Height, size.Height));
                form.Size = size;
            }
            //
            location.X = Math.Max(workingArea.Left, Math.Min(location.X, workingArea.Right - form.Width));
            location.Y = Math.Max(workingArea.Top, Math.Min(location.Y, workingArea.Bottom - form.Height));
            //
            if (form.Location != location) form.Location = location;
        }
    }
}
