// Transport fixture only; this executable is not a solver.
using System.Diagnostics;
using System.Text.Json;
if(args.Length==0)return 2;
if(args[0]=="echo") {Console.WriteLine(JsonSerializer.Serialize(new{args=args.Skip(1).ToArray(),cwd=Environment.CurrentDirectory,env=Environment.GetEnvironmentVariable("PREPOMAXX_PROBE"),marker=File.Exists("working-marker")?File.ReadAllText("working-marker"):null}));Console.Error.WriteLine("probe stderr");return 0;}
if(args[0]=="fail") {Console.Error.WriteLine("intentional exit seven");return 7;}
if(args[0]=="stream") {for(int i=0;i<20000;i++){Console.WriteLine("out "+i);Console.Error.WriteLine("err "+i);}return 0;}
if(args[0]=="sleep") {Console.WriteLine("ready");Console.Out.Flush();Thread.Sleep(30000);return 0;}
if(args[0]=="child") {
 var info=new ProcessStartInfo(Environment.ProcessPath!){UseShellExecute=false};info.ArgumentList.Add(typeof(Program).Assembly.Location);info.ArgumentList.Add("sleep");
 using var child=Process.Start(info)!;File.WriteAllText("child.pid",child.Id.ToString());Console.WriteLine("child "+child.Id);Thread.Sleep(30000);return 0;
}
return 2;
namespace PrePoMaxXProbe { public sealed class Marker { } }
