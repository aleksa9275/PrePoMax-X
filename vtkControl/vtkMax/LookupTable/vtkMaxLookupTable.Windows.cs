// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
// Licensed under the root LICENSE. Original bitmap output moved unchanged.
using System.Drawing;
using System.Drawing.Imaging;
namespace vtkControl { public partial class vtkMaxLookupTable {
        private void WriteTexture(int width, int height, string filePath)
        {
            using (Bitmap bmp = new Bitmap(width, height, PixelFormat.Format32bppArgb))
            {
                Color[] colors = _colors.Length == 0 ? new Color[] { Color.White } : _colors;
                for (int y = 0; y < height; y++)
                {
                    int colorIndex = (int)((long)(height - y - 1) * colors.Length / height);
                    for (int x = 0; x < width; x++) bmp.SetPixel(x, y, colors[colorIndex]);
                }
                bmp.Save(filePath, ImageFormat.Png);
            }
        }
}}
