// Portable integration for original amplitudes and prescribed-temperature fields.
// Reuses original engineering and keyword classes, without numerical changes.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using CaeGlobals;
using CaeMesh;
using FileInOut.Output.Calculix;

namespace CaeModel
{
    public static class AnalysisModelExtensions
    {
        internal static Dictionary<string,AmplitudeTabular> Amplitudes(IEnumerable<AmplitudeTabular> values)
        {
            var result=new Dictionary<string,AmplitudeTabular>(StringComparer.OrdinalIgnoreCase);
            foreach(var a in values??Array.Empty<AmplitudeTabular>()) {
                if(a==null || a.GetType()!=typeof(AmplitudeTabular) || !a.Active || !a.Valid)throw new CaeException("Active tabular amplitudes required.");
                StaticAnalysisDeckWriter.Name(a.Name);
                if(a.Name.Equals(Amplitude.DefaultAmplitudeName,StringComparison.OrdinalIgnoreCase) || result.ContainsKey(a.Name) || result.Count>=100 ||
                    !Enum.IsDefined(typeof(AmplitudeTimeSpanEnum),a.TimeSpan) || !Finite(a.ShiftX) || !Finite(a.ShiftY) ||
                    a.TimeAmplitude==null || a.TimeAmplitude.Length<2 || a.TimeAmplitude.Length>10000 ||
                    a.TimeAmplitude.Any(r=>r==null || r.Length!=2 || r.Any(v=>!Finite(v))) ||
                    a.TimeAmplitude.Skip(1).Where((r,i)=>r[0]<=a.TimeAmplitude[i][0]).Any())
                    throw new CaeException("Unique bounded tabular amplitudes with finite shifts and strictly increasing times required.");
                result.Add(a.Name,a);
            }
            return result;
        }
        internal static void Reference(string name,Dictionary<string,AmplitudeTabular> amplitudes)
        {
            if(name!=Amplitude.DefaultAmplitudeName && !amplitudes.ContainsKey(name))throw new CaeException("Missing amplitude: "+name);
        }
        internal static void WriteAmplitudes(StringBuilder text,Dictionary<string,AmplitudeTabular> amplitudes)
        {
            foreach(var a in amplitudes.Values)Append(text,new CalAmplitude(a));
        }
        internal static void WriteMechanicalInitial(StringBuilder text,InpMeshData mesh,string temperature)
        {
            if(temperature==null)return;
            var initial=new InitialTemperature("Initial-temperature","",RegionTypeEnum.NodeSetName,0);initial.Temperature.SetEquation(temperature);
            if(!Finite(initial.Temperature.Value) || temperature.Length>4096)throw new CaeException("Finite bounded initial temperature required.");
            // Original per-node constructor and writer preserve the mesh/set namespace.
            foreach(int id in mesh.Nodes.Keys.OrderBy(i=>i)) {
                var value=new InitialTemperature("Initial-temperature",id,initial.Temperature.Value);
                Append(text,new CalInitialTemperature(value));
            }
        }
        internal static List<CalculixKeyword> Temperatures(InpMeshData mesh,Step step,string initialTemperature,Dictionary<string,AmplitudeTabular> amplitudes)
        {
            var result=new List<CalculixKeyword>();var covered=new HashSet<int>();
            if(step.DefinedFields.Count>1000)throw new CaeException("Temperature field limit exceeded.");
            foreach(var entry in step.DefinedFields) {
                var t=entry.Value as DefinedTemperature;
                if(t==null || t.GetType()!=typeof(DefinedTemperature) || entry.Key!=t.Name || !t.Active || !t.Valid ||
                    t.Type!=DefinedTemperatureTypeEnum.ByValue || t.RegionType!=RegionTypeEnum.NodeSetName ||
                    t.DistributionName!=Distribution.DefaultDistributionName || t.CreationData!=null || t.CreationIds?.Length>0 || !Finite(t.Temperature.Value))
                    throw new CaeException("Finite prescribed temperature fields on named node sets required.");
                StaticAnalysisDeckWriter.Name(t.Name);StaticAnalysisDeckWriter.Name(t.RegionName);Reference(t.AmplitudeName,amplitudes);
                var keys=mesh.NodeSets.Keys.Where(k=>string.Equals(k,t.RegionName,StringComparison.OrdinalIgnoreCase)).ToArray();
                if(keys.Length!=1 || mesh.NodeSets[keys[0]].Length==0)throw new CaeException("Missing temperature field region.");
                foreach(int id in mesh.NodeSets[keys[0]])if(!covered.Add(id))throw new CaeException("Overlapping prescribed temperature fields.");
                result.Add(new CalDefinedTemperature(t));
            }
            if(result.Count>0 && (initialTemperature==null || !covered.SetEquals(mesh.Nodes.Keys)))
                throw new CaeException("Explicit initial temperature and full nonoverlapping nodal temperature-field coverage required.");
            return result;
        }
        private static bool Finite(double v) {return !double.IsNaN(v) && !double.IsInfinity(v);}
        private static void Append(StringBuilder t,CalculixKeyword k) {t.Append(k.GetKeywordString()).Append(k.GetDataString());}
    }
}
