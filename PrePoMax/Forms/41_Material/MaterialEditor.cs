// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
// Licensed under the terms defined in the root LICENSE file.
// Nonvisual FrmMaterial behaviour shared by the original and portable forms.
using System;
using System.Collections.Generic;
using CaeGlobals;
using CaeModel;
using PrePoMax.PropertyViews;
namespace PrePoMax
{
    public static class MaterialEditor
    {
        public static KeyValuePair<string, MaterialProperty>[] PropertyTemplates()
        {
            return new[]
            {
                new KeyValuePair<string, MaterialProperty>("Density", new Density(new double[][] { new double[] { 0, 0 } })),
                new KeyValuePair<string, MaterialProperty>("Slip Wear", new SlipWear(0, 0)),
                new KeyValuePair<string, MaterialProperty>("Elastic", new Elastic(new double[][] { new double[] { 0, 0, 0 } })),
                new KeyValuePair<string, MaterialProperty>("Engineering Constants", new ElasticEngineeringConstants(new double[][] { new double[ElasticEngineeringConstants.NumberOfValues] })),
                new KeyValuePair<string, MaterialProperty>("Lamina", new ElasticLamina(new double[][] { new double[ElasticLamina.NumberOfValues] })),
                new KeyValuePair<string, MaterialProperty>("Plastic", new Plastic(new double[][] { new double[] { 0, 0, 0 } })),
                new KeyValuePair<string, MaterialProperty>("Thermal Expansion", new ThermalExpansion(new double[][] { new double[] { 0, 0 } })),
                new KeyValuePair<string, MaterialProperty>("Thermal Conductivity", new ThermalConductivity(new double[][] { new double[] { 0, 0 } })),
                new KeyValuePair<string, MaterialProperty>("Specific Heat", new SpecificHeat(new double[][] { new double[] { 0, 0 } }))
            };
        }
        public static IEnumerable<ViewMaterialProperty> CreateViews(Material material)
        {
            foreach (MaterialProperty property in material.Properties)
            {
                ViewMaterialProperty view;
                if (property is Density den) view = new ViewDensity(den);
                else if (property is SlipWear sw) view = new ViewSlipWear(sw);
                else if (property is Elastic el) view = new ViewElastic(el);
                else if (property is ElasticEngineeringConstants eec)
                    view = new ViewElasticEngineeringConstants(eec);
                else if (property is ElasticLamina ela)
                    view = new ViewElasticLamina(ela);
                else if (property is ElasticWithDensity ewd)
                {
                    view = new ViewElasticWithDensity(ewd);
                }
                else if (property is Plastic pl) view = new ViewPlastic(pl);
                else if (property is ThermalExpansion te)
                    view = new ViewThermalExpansion(te, material.TemperatureDependent);
                else if (property is ThermalConductivity tc) view = new ViewThermalConductivity(tc);
                else if (property is SpecificHeat sh) view = new ViewSpecificHeat(sh);
                else throw new NotSupportedException();
                yield return view;
            }
        }
        public static Material Build(string name, string description, bool temperatureDependent,
                                     IEnumerable<ViewMaterialProperty> views)
        {
            Material material = new Material(name);
            material.Description = description;
            material.TemperatureDependent = temperatureDependent;
            //
            ViewMaterialProperty property;
            MaterialProperty materialProperty;
            int elasticityCount = 0;
            int densityCount = 0;
            foreach (ViewMaterialProperty view in views)
            {
                property = view;
                if (property is ViewElastic ||
                    property is ViewElasticEngineeringConstants ||
                    property is ViewElasticLamina ||
                    property is ViewElasticWithDensity)
                {
                    elasticityCount++;
                    if (elasticityCount > 1) throw new CaeException("A material can contain only one elastic property.");
                }
                if (property is ViewDensity || property is ViewElasticWithDensity)
                {
                    densityCount++;
                    if (densityCount > 1) throw new CaeException("A material can contain only one density.");
                }
                materialProperty = property.GetBase();
                // Check equations
                materialProperty.CheckEquations();
                //
                if (property is ViewDensity vd)
                {
                    for (int i = 0; i < vd.DataPoints.Count; i++)
                    {
                        if (vd.DataPoints[i].Density.Value <= 0) throw new CaeException("The density must be larger than 0.");
                    }
                }
                else if (property is ViewElastic ve && ve.GetYoungsModulusValue() <= 0)
                {
                    throw new CaeException("The Young's modulus must be larger than 0.");
                }
                else if (property is ViewElasticEngineeringConstants && temperatureDependent)
                {
                    ((ElasticEngineeringConstants)materialProperty).CheckTemperatures();
                }
                else if (property is ViewElasticLamina && temperatureDependent)
                {
                    ((ElasticLamina)materialProperty).CheckTemperatures();
                }
                else if (property is ViewElasticWithDensity ewd)
                {
                    if (ewd.GetYoungsModulusValue() <= 0) throw new CaeException("The Young's modulus must be larger than 0.");
                    if (ewd.GetDensityValue() <= 0) throw new CaeException("The density must be larger than 0.");
                }
                else if (property is ViewThermalExpansion vex)
                {
                    for (int i = 0; i < vex.DataPoints.Count; i++)
                    {
                        if (vex.DataPoints[i].ThermalExpansion.Value <= 0)
                            throw new CaeException("The thermal expansion coefficient must be larger than 0.");
                    }
                }
                else if (property is ViewThermalConductivity vtc)
                {
                    for (int i = 0; i < vtc.DataPoints.Count; i++)
                    {
                        if (vtc.DataPoints[i].ThermalConductivity.Value <= 0)
                            throw new CaeException("The thermal conductivity coefficient must be larger than 0.");
                    }
                }
                else if (property is ViewSpecificHeat vsh)
                {
                    for (int i = 0; i < vsh.DataPoints.Count; i++)
                    {
                        if (vsh.DataPoints[i].SpecificHeat.Value <= 0)
                            throw new CaeException("The thermal conductivity coefficient must be larger than 0.");
                    }
                }
                else if (property is ViewSlipWear vsw)
                {
                    if (vsw.GetHardnessValue() <= 0) throw new CaeException("The hardness must be larger than 0.");
                    if (vsw.GetWearCoefficientValue() <= 0) throw new CaeException("The wear coefficient must be larger than 0.");
                }
                //
                material.AddProperty(materialProperty);
            }
            return material;
        }
    }
}
