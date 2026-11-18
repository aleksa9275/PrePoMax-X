// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://github.com/PrePoMax/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace vtkControl
{
    public partial class vtkMaxLookupTable
    {
        // Variables                                                                                                                
        private double _minValue;
        private double _maxValue;
        private Color[] _colors;
        private bool _smoothColors;


        // Properties
        public Color[] Colors { get { return _colors; } set { _colors = value; } }
        public bool SmoothColors { get { return _smoothColors; } }


        // Constructors                                                                                                             
        public vtkMaxLookupTable()
        {
            _minValue = 0.0;
            _maxValue = 0.0;
            _colors = new Color[0];
            _smoothColors = false;
        }
        public vtkMaxLookupTable(double minValue, double maxValue, Color[] colors, bool smoothColors)
        {
            _minValue = minValue;
            _maxValue = maxValue;
            _colors = colors;
            _smoothColors = smoothColors;
        }



        // Methods                                                                                                                  
        public double GetNormalizedValue(double value)
        {
            if (value <= _minValue) return 0.0;
            if (value >= _maxValue) return 1.0;
            double normalizedValue = (value - _minValue) / (_maxValue - _minValue);
            return normalizedValue;
        }
        public int GetColorIndex(double value)
        {
            if (value <= _minValue) return 0;
            if (value >= _maxValue) return _colors.Length - 1;
            double normalizedValue = (value - _minValue) / (_maxValue - _minValue);
            int colorIndex = (int)(normalizedValue * _colors.Length);
            return colorIndex;
        }
        public int GetRecommendedTextureHeight()
        {
            if (_colors.Length == 0) return 1;
            else if (_smoothColors) return _colors.Length;
            else return _colors.Length * 200;
        }
        public void WriteAsTexture(int width, int height, string filePath)
        {
            if (width < 1) throw new ArgumentOutOfRangeException(nameof(width));
            if (height < 1) throw new ArgumentOutOfRangeException(nameof(height));
            //
            WriteTexture(width, height, filePath);
        }
    }
}
