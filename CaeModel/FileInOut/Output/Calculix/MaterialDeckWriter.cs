// PrePoMax-X material transport boundary. Reuses Matej Borovinšek's original
// material/equation types and CalMaterial/CalElastic writers. See root LICENSE.
using System;
using System.Globalization;
using System.Text.RegularExpressions;
using CaeGlobals;
using FileInOut.Output.Calculix;

namespace CaeModel
{
    public static class MaterialDeckWriter
    {
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
