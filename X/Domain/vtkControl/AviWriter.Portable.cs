// PrePoMax-X: the AVI writer of vtkControl (Tools/AviWriter.cs) without Video for Windows (avifil32 is Windows
// only). Same calls: Start, Write (RGB rows, bottom row first, as the native view reads them), Dispose. The frames
// are written uncompressed (24-bit DIB, the format the original hands to its compressor); the Microsoft Video 1
// compressor and its options dialog exist only on Windows, so quality and the prompt are not used here.
// RIFF layout: https://learn.microsoft.com/windows/win32/directshow/avi-riff-file-reference
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using CaeGlobals;

namespace vtkControl
{
    public sealed class AviWriter : IDisposable
    {
        // Variables
        private FileStream _file;
        private int _width;
        private int _height;
        private int _rowLength;
        private byte[] _frame;
        private int _rate;
        private long _moviStart;
        private long _avihFramesOffset;
        private long _strhLengthOffset;
        private readonly List<long> _offsets = new List<long>();


        // Methods
        public bool Start(string fileName, int width, int height, int rate, int quality, bool promptCompressionOptions)
        {
            _width = width;
            _height = height;
            _rate = rate;
            _rowLength = (width * 3 + 3) / 4 * 4;
            _frame = new byte[_rowLength * height];
            try { _file = new FileStream(fileName, FileMode.Create, FileAccess.ReadWrite); }
            catch (Exception ex) when (ex is IOException || ex is UnauthorizedAccessException)
            {
                throw new CaeException("Unable to open " + fileName + ".");
            }
            //
            var w = new BinaryWriter(_file, Encoding.ASCII, true);
            w.Write(Encoding.ASCII.GetBytes("RIFF")); w.Write(0); w.Write(Encoding.ASCII.GetBytes("AVI "));
            // hdrl: avih + strl(strh, strf)
            w.Write(Encoding.ASCII.GetBytes("LIST")); w.Write(4 + 8 + 56 + 8 + 4 + 8 + 56 + 8 + 40); w.Write(Encoding.ASCII.GetBytes("hdrl"));
            w.Write(Encoding.ASCII.GetBytes("avih")); w.Write(56);
            w.Write(1000000 / Math.Max(1, rate)); w.Write(_frame.Length * rate); w.Write(0); w.Write(0x10);
            _avihFramesOffset = _file.Position; w.Write(0);
            w.Write(0); w.Write(1); w.Write(_frame.Length); w.Write(width); w.Write(height); w.Write(0); w.Write(0); w.Write(0); w.Write(0);
            w.Write(Encoding.ASCII.GetBytes("LIST")); w.Write(4 + 8 + 56 + 8 + 40); w.Write(Encoding.ASCII.GetBytes("strl"));
            w.Write(Encoding.ASCII.GetBytes("strh")); w.Write(56);
            w.Write(Encoding.ASCII.GetBytes("vids")); w.Write(Encoding.ASCII.GetBytes("DIB "));
            w.Write(0); w.Write((short)0); w.Write((short)0); w.Write(0); w.Write(1); w.Write(rate); w.Write(0);
            _strhLengthOffset = _file.Position; w.Write(0);
            w.Write(_frame.Length); w.Write(-1); w.Write(0); w.Write((short)0); w.Write((short)0); w.Write((short)width); w.Write((short)height);
            w.Write(Encoding.ASCII.GetBytes("strf")); w.Write(40);
            w.Write(40); w.Write(width); w.Write(height); w.Write((short)1); w.Write((short)24); w.Write(0); w.Write(_frame.Length);
            w.Write(0); w.Write(0); w.Write(0); w.Write(0);
            w.Write(Encoding.ASCII.GetBytes("LIST")); w.Write(0); w.Write(Encoding.ASCII.GetBytes("movi"));
            _moviStart = _file.Position - 4;
            w.Flush();
            return true;
        }
        // RGB rows, bottom row first, as the native view reads them
        public void Write(byte[] rgb)
        {
            if (_file == null) return;
            for (int y = 0; y < _height; y++)
            {
                int read = y * _width * 3;
                int write = y * _rowLength;
                for (int x = 0; x < _width; x++)
                {
                    _frame[write++] = rgb[read + 2];
                    _frame[write++] = rgb[read + 1];
                    _frame[write++] = rgb[read];
                    read += 3;
                }
            }
            _offsets.Add(_file.Position - _moviStart);
            var w = new BinaryWriter(_file, Encoding.ASCII, true);
            w.Write(Encoding.ASCII.GetBytes("00db")); w.Write(_frame.Length); w.Write(_frame);
            w.Flush();
        }
        public void Dispose()
        {
            if (_file == null) return;
            var w = new BinaryWriter(_file, Encoding.ASCII, true);
            long moviEnd = _file.Position;
            w.Write(Encoding.ASCII.GetBytes("idx1")); w.Write(_offsets.Count * 16);
            foreach (long offset in _offsets)
            {
                w.Write(Encoding.ASCII.GetBytes("00db")); w.Write(0x10); w.Write((int)offset); w.Write(_frame.Length);
            }
            long end = _file.Position;
            _file.Position = 4; w.Write((int)(end - 8));
            _file.Position = _moviStart - 4; w.Write((int)(moviEnd - _moviStart));
            _file.Position = _avihFramesOffset; w.Write(_offsets.Count);
            _file.Position = _strhLengthOffset; w.Write(_offsets.Count);
            w.Flush();
            _file.Dispose();
            _file = null;
        }
    }
}
