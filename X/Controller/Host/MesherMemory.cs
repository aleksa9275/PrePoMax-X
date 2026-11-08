using System;
using System.Diagnostics;
using System.IO;
using System.Globalization;
using System.Linq;
using System.Text.RegularExpressions;
namespace PrePoMax
{
    internal static class MesherMemory
    {
        public static float AvailableMegabytes
        {
            get
            {
                if (OperatingSystem.IsLinux())
                {
                    string line = File.ReadLines("/proc/meminfo").Single(l => l.StartsWith("MemAvailable:"));
                    return float.Parse(line.Split((char[])null,StringSplitOptions.RemoveEmptyEntries)[1],CultureInfo.InvariantCulture)/1024;
                }
                if (OperatingSystem.IsMacOS())
                {
                    using var p = Process.Start(new ProcessStartInfo("/usr/bin/vm_stat") {RedirectStandardOutput=true,UseShellExecute=false});
                    string text=p.StandardOutput.ReadToEnd(); p.WaitForExit();
                    if(p.ExitCode!=0)throw new IOException("vm_stat could not report available physical memory.");
                    long pageSize=long.Parse(Regex.Match(text,@"page size of (\d+) bytes").Groups[1].Value,CultureInfo.InvariantCulture);
                    long pages=Regex.Matches(text,@"Pages (?:free|inactive|speculative):\s+(\d+)").Sum(m=>long.Parse(m.Groups[1].Value,CultureInfo.InvariantCulture));
                    return (float)(pages*pageSize/(1024.0*1024));
                }
                if(OperatingSystem.IsWindows())
                {
                    var status=new MemoryStatus {Length=(uint)System.Runtime.InteropServices.Marshal.SizeOf<MemoryStatus>()};
                    if(!GlobalMemoryStatusEx(ref status))throw new System.ComponentModel.Win32Exception();
                    return status.AvailablePhysical/(1024f*1024);
                }
                throw new PlatformNotSupportedException("Available physical memory is not implemented on this OS.");
            }
        }
        [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
        private struct MemoryStatus {public uint Length,Load;public ulong TotalPhysical,AvailablePhysical,TotalPageFile,AvailablePageFile,TotalVirtual,AvailableVirtual,AvailableExtendedVirtual;}
        [System.Runtime.InteropServices.DllImport("kernel32.dll",SetLastError=true)]
        [return:System.Runtime.InteropServices.MarshalAs(System.Runtime.InteropServices.UnmanagedType.Bool)]
        private static extern bool GlobalMemoryStatusEx(ref MemoryStatus status);
    }
}
