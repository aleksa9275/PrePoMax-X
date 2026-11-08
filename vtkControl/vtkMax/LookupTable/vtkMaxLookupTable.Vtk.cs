// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://gitlab.com/MatejB/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

// PrePoMax-X: constructors taking a Kitware (ActiViz) lookup table, moved verbatim
// from vtkMaxLookupTable.cs so the data class builds without ActiViz (D062).

using System.Drawing;
using Kitware.VTK;

namespace vtkControl
{
    public partial class vtkMaxLookupTable
    {
        public vtkMaxLookupTable(vtkLookupTable lookupTable)
            : this(lookupTable, false)
        {
        }
        public vtkMaxLookupTable(vtkLookupTable lookupTable, bool smoothColors)
        {
            _minValue = lookupTable.GetTableRange()[0];
            _maxValue = lookupTable.GetTableRange()[1];
            _smoothColors = smoothColors;
            
            int numberOfColors = (int)lookupTable.GetNumberOfColors();
            _colors = new Color[numberOfColors];
            for (int i = 0; i < numberOfColors; i++)
            {
                double[] rgba = lookupTable.GetTableValue(i);
                _colors[i] = Color.FromArgb(
                    (int)(rgba[3] * 255),
                    (int)(rgba[0] * 255),
                    (int)(rgba[1] * 255),
                    (int)(rgba[2] * 255)
                );
            }
        }
    }
}
