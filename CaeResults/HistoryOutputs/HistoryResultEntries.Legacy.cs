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
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using CaeMesh;
using CaeGlobals;
using System.Runtime.Serialization;
using System.ComponentModel;
using System.IO.Compression;
using System.IO;
using static CaeGlobals.Geometry2;

namespace CaeResults
{
    public partial class HistoryResultEntries
    {
        // Static methods                                                                                                           
        public static void WriteToBinaryWriter(HistoryResultEntries historyResultEntries, BinaryWriter bw)
        {
            if (historyResultEntries == null)
            {
                bw.Write((int)0);
            }
            else
            {
                bw.Write((int)1);
                // Name
                bw.Write(historyResultEntries.Name);
                // Time
                if (historyResultEntries.Time == null) bw.Write((int)0);
                else
                {
                    bw.Write((int)1);
                    bw.Write((int)historyResultEntries.Time.Count);
                    foreach (var time in historyResultEntries.Time) bw.Write(time);
                }
                // Values
                if (historyResultEntries.Values == null) bw.Write((int)0);
                else
                {
                    bw.Write((int)1);
                    bw.Write((int)historyResultEntries.Values.Count);
                    foreach (var value in historyResultEntries.Values) bw.Write(value);
                }
                // Count
                if (historyResultEntries.Count == null) bw.Write((int)0);
                else
                {
                    bw.Write((int)1);
                    bw.Write((int)historyResultEntries.Count.Count);
                    foreach (var count in historyResultEntries.Count) bw.Write(count);
                }
                // Local
                bw.Write(historyResultEntries.Local);
                // Unit
                if (historyResultEntries.Unit == null) bw.Write("@null#");
                else bw.Write(historyResultEntries.Unit);
            }
        }
        public static void WriteToFileStream(HistoryResultEntries historyResultEntries, FileStream fileStream,
                                             CompressionLevel compressionLevel)
        {
            if (historyResultEntries == null)
            {
                Tools.WriteIntToFileStream(fileStream, 0);
            }
            //
            else
            {
                Tools.WriteIntToFileStream(fileStream, 1);
                //
                using (BinaryWriter bw = new BinaryWriter(new MemoryStream()))
                {
                    WriteToBinaryWriter(historyResultEntries, bw);
                    // Rewind the writer
                    bw.Flush();
                    bw.BaseStream.Position = 0;
                    // Compress the writer
                    byte[] compressedData = Tools.Compress(bw.BaseStream, compressionLevel);
                    // Write the length of the compressed data
                    Tools.WriteIntToFileStream(fileStream, compressedData.Length);
                    // Write the compressed data
                    fileStream.Write(compressedData, 0, compressedData.Length);
                }
            }
            
        }
        public static HistoryResultEntries ReadFromBinaryReader(BinaryReader br, int version)
        {
            int numItems;
            HistoryResultEntries historyResultEntries;
            //
            int exists = br.ReadInt32();
            if (exists == 1)
            {
                // Name
                string name = br.ReadString();
                historyResultEntries = new HistoryResultEntries(name, false);
                // Time
                exists = br.ReadInt32();
                if (exists == 1)
                {
                    numItems = br.ReadInt32();
                    for (int i = 0; i < numItems; i++) historyResultEntries.Time.Add(br.ReadDouble());
                }
                // Values
                exists = br.ReadInt32();
                if (exists == 1)
                {
                    numItems = br.ReadInt32();
                    for (int i = 0; i < numItems; i++) historyResultEntries.Values.Add(br.ReadDouble());
                }
                // Count
                exists = br.ReadInt32();
                if (exists == 1)
                {
                    numItems = br.ReadInt32();
                    for (int i = 0; i < numItems; i++) historyResultEntries.Count.Add(br.ReadInt32());
                }
                // Local
                historyResultEntries.Local = br.ReadBoolean();
                // Unit
                historyResultEntries.Unit = br.ReadString();
                if (historyResultEntries.Unit == "@null#") historyResultEntries.Unit = null;
                //
                return historyResultEntries;
            }
            return null;
        }
        public static HistoryResultEntries ReadFromFileStream(FileStream fileStream, int version)
        {
            int exists = Tools.ReadIntFromFileStream(fileStream);
            //
            if (exists == 1)
            {
                int numOfBytes = Tools.ReadIntFromFileStream(fileStream);
                byte[] compressedData = new byte[numOfBytes];
                fileStream.Read(compressedData, 0, compressedData.Length);
                //
                HistoryResultEntries historyResultEntries;
                using (MemoryStream memoryStream = new MemoryStream(compressedData))
                using (BinaryReader br = new BinaryReader(Tools.Decompress(memoryStream)))
                {
                    historyResultEntries = ReadFromBinaryReader(br, version);
                }
                return historyResultEntries;
            }
            else return null;
        }


    }
}
