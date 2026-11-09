using System;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Buffers.Binary;
using System.Text;
namespace vtkControl
{
    public partial class vtkMaxLookupTable
    {
        // Original texture row/color mapping; only the PNG encoding is platform code.
        public void SetExportData(double minimum,double maximum,Color[] colors,bool smooth){_minValue=minimum;_maxValue=maximum;_colors=colors;_smoothColors=smooth;}
        private void WriteTexture(int width, int height, string filePath)
        {
            using var pixels = new MemoryStream();
            using (var compressed = new ZLibStream(pixels, CompressionLevel.Optimal, true))
            {
                Color[] colors = _colors.Length == 0 ? new Color[] { Color.White } : _colors;
                for (int y = 0; y < height; y++)
                {
                    compressed.WriteByte(0); // PNG row with no filtering
                    int colorIndex = (int)((long)(height - y - 1) * colors.Length / height);
                    Color color = colors[colorIndex];
                    for (int x = 0; x < width; x++)
                        compressed.Write(new byte[] { color.R, color.G, color.B, color.A });
                }
            }
            using var output = File.Create(filePath);
            output.Write(new byte[] {137,80,78,71,13,10,26,10});
            byte[] header = new byte[13];
            BinaryPrimitives.WriteInt32BigEndian(header.AsSpan(0,4),width);
            BinaryPrimitives.WriteInt32BigEndian(header.AsSpan(4,4),height);
            header[8]=8; header[9]=6; // 8-bit RGBA
            Chunk(output,"IHDR",header); Chunk(output,"IDAT",pixels.ToArray()); Chunk(output,"IEND",Array.Empty<byte>());
        }
        static void Chunk(Stream output,string kind,byte[] data)
        {
            byte[] length=new byte[4]; BinaryPrimitives.WriteInt32BigEndian(length,data.Length);output.Write(length);
            byte[] type=Encoding.ASCII.GetBytes(kind);output.Write(type);output.Write(data);
            uint crc=0xffffffff;
            foreach(byte value in type)crc=Crc(crc,value);
            foreach(byte value in data)crc=Crc(crc,value);
            BinaryPrimitives.WriteUInt32BigEndian(length,crc^0xffffffff);output.Write(length);
        }
        static uint Crc(uint crc,byte value)
        {
            crc^=value;for(int bit=0;bit<8;bit++)crc=(crc&1)!=0?(crc>>1)^0xedb88320:crc>>1;return crc;
        }
    }
}
