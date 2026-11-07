// PrePoMax-X material transport boundary. Reuses Matej Borovinšek's original
// material/equation types and CalMaterial/CalElastic writers. See root LICENSE.
using System;
using System.Globalization;
using System.Linq;
using System.Text.RegularExpressions;
using CaeGlobals;
using FileInOut.Output.Calculix;

namespace CaeModel
{
    public static class MaterialDeckWriter
    {
        public static string WriteDensity(Density density)
        {
            var rows = density == null ? null : density.DensityTemp;
            if (rows == null || rows.Length != 1 || rows[0] == null || rows[0].Length != 2 || rows[0].Any(v=>v==null))
                throw new CaeException("One complete density row is required.");
            double value=rows[0][0].Value, temperature=rows[0][1].Value;
            if (!Finite(value) || value<=0 || !Finite(temperature)) throw new CaeException("Density must be finite and positive.");
            var previous=CultureInfo.CurrentCulture;
            try {
                CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
                var keyword=new CalDensity(new Density(new[]{new[]{value,temperature}}),false);
                return keyword.GetKeywordString()+keyword.GetDataString();
            } finally { CultureInfo.CurrentCulture=previous; }
        }

        public static string WriteMechanical(Material material)
        {
            if (material==null || material.GetType()!=typeof(Material) || material.TemperatureDependent || !material.Active || !material.Valid ||
                material.Properties.Any(p=>p==null || (p.GetType()!=typeof(Elastic) && p.GetType()!=typeof(Density) && p.GetType()!=typeof(Plastic) && p.GetType()!=typeof(ThermalExpansion))) ||
                material.Properties.OfType<Elastic>().Count()!=1 || material.Properties.OfType<Density>().Count()>1 || material.Properties.OfType<Plastic>().Count()>1 || material.Properties.OfType<ThermalExpansion>().Count()>1)
                throw new NotSupportedException("Provide isotropic elasticity with optional density and plasticity.");
            var elasticOnly=new Material(material.Name);elasticOnly.AddProperty(material.Properties.OfType<Elastic>().Single());
            string text=WriteIsotropic(elasticOnly);
            var density=material.Properties.OfType<Density>().SingleOrDefault();
            if (density!=null) text+=WriteDensity(density);
            var expansion=material.Properties.OfType<ThermalExpansion>().SingleOrDefault();
            if(expansion!=null) {
                var er=expansion.ThermalExpansionTemp;
                if(er==null || er.Length!=1 || er[0]==null || er[0].Length!=2 || er[0].Any(v=>v==null || !Finite(v.Value)) || !Finite(expansion.ZeroTemperature.Value))
                    throw new CaeException("One finite constant thermal expansion row and reference temperature required.");
                double coefficient=er[0][0].Value,temperature=er[0][1].Value,reference=expansion.ZeroTemperature.Value;
                var culture=CultureInfo.CurrentCulture;
                try {
                    CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
                    var snapshot=new ThermalExpansion(new[]{new[]{coefficient,temperature}});snapshot.ZeroTemperature.SetEquationFromValue(reference);
                    var keyword=new CalThermalExpansion(snapshot,false);text+=keyword.GetKeywordString()+keyword.GetDataString();
                } finally {CultureInfo.CurrentCulture=culture;}
            }
            var plastic=material.Properties.OfType<Plastic>().SingleOrDefault();
            if (plastic==null) return text;
            var rows=plastic.StressStrainTemp;
            if (rows==null || rows.Length<1 || rows.Length>10000 || !Enum.IsDefined(typeof(PlasticHardening),plastic.Hardening) ||
                rows.Any(r=>r==null || r.Length!=3 || r.Any(v=>v==null))) throw new CaeException("Complete plastic stress/strain rows are required.");
            var values=rows.Select(r=>r.Select(v=>v.Value).ToArray()).ToArray();
            if (values.Any(r=>r.Any(v=>!Finite(v)) || r[0]<=0 || r[1]<0) || values[0][1]!=0 ||
                values.Skip(1).Where((r,i)=>r[1]<=values[i][1]).Any())
                throw new CaeException("Plastic data require positive stress, zero initial plastic strain and increasing strain values.");
            var previous=CultureInfo.CurrentCulture;
            try {
                CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
                var snapshot=new Plastic(values){Hardening=plastic.Hardening};
                var keyword=new CalPlastic(snapshot,false);
                return text+keyword.GetKeywordString()+keyword.GetDataString();
            } finally { CultureInfo.CurrentCulture=previous; }
        }

        // A material fragment only: no section, step, BC/load or complete analysis.
        // Values use the caller's existing converter/unit context; this method does
        // not select a unit system or modify the supplied engineering objects.
        public static string WriteIsotropic(Material material)
        {
            if (material == null) throw new ArgumentNullException("material");
            if (material.Name == null || material.Name.Length > 80 ||
                !Regex.IsMatch(material.Name, @"\A[A-Za-z_][A-Za-z0-9_-]*\z"))
                throw new CaeException("Material export requires a simple ASCII keyword name of at most 80 characters.");
            if (!material.Active || !material.Valid)
                throw new CaeException("Material export requires an active, valid material.");
            if (material.TemperatureDependent || material.Properties.Count != 1 ||
                !(material.Properties[0] is Elastic))
                throw new NotSupportedException("This boundary supports one temperature-independent isotropic elastic property only.");
            var elastic = (Elastic)material.Properties[0];
            var rows = elastic.YoungsPoissonsTemp;
            if (rows == null || rows.Length != 1 || rows[0] == null || rows[0].Length != 3 ||
                rows[0][0] == null || rows[0][1] == null || rows[0][2] == null)
                throw new CaeException("One complete elastic data row is required.");
            // Evaluate in the caller's culture before entering the deck's invariant
            // formatting context. A snapshot avoids mutating equations or units.
            double youngs = rows[0][0].Value;
            double poisson = rows[0][1].Value;
            double temperature = rows[0][2].Value;
            if (!Finite(youngs) || !Finite(poisson) || !Finite(temperature) || youngs <= 0 ||
                poisson <= -1 || poisson >= 0.5)
                throw new CaeException("Isotropic export requires finite E > 0 and -1 < Poisson ratio < 0.5.");
            var previousCulture = CultureInfo.CurrentCulture;
            try
            {
                CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
                var evaluated = new Elastic(new double[][] { new double[] { youngs, poisson, temperature } });
                var name = new CalMaterial(material);
                var property = new CalElastic(evaluated, false);
                return name.GetKeywordString() + name.GetDataString() +
                       property.GetKeywordString() + property.GetDataString();
            }
            finally { CultureInfo.CurrentCulture = previousCulture; }
        }

        private static bool Finite(double value) { return !double.IsNaN(value) && !double.IsInfinity(value); }
    }
}
