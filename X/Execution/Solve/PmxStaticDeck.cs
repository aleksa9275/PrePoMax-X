using System.Text.Json;
using System.Text.Json.Serialization;
using CaeGlobals;
using CaeModel;
using FileInOut.Output.Calculix;
using PrePoMaxX.MeshDeck;
using PrePoMaxX.StaticDeck;

namespace PrePoMaxX.Solve;

internal static class PmxStaticDeck
{
    internal static (string Text, double MassDensity, string Material, string Step) Build(
        InpMeshData mesh, string definition)
    {
        using var input = File.OpenRead(definition);
        if (input.Length > AnalysisFiles.MaximumDefinitionBytes)
            throw new InvalidDataException("Controlled definition exceeds the byte limit.");
        var model = JsonSerializer.Deserialize<ControlledDefinition>(input,
            new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
                RespectRequiredConstructorParameters = true,
                AllowDuplicateProperties = false,
                MaxDepth = 32,
            })
            ?? throw new InvalidDataException("Missing controlled definition.");
        var (materials, sections, step) = AnalysisFiles.Create(model.Analysis);
        if (materials.Length != 1 || sections.Length != 1 || model.Density is not { Length: 2 } ||
            model.Density.Any(string.IsNullOrEmpty) || model.Outputs is not { Length: > 0 and <= 100 } ||
            step.HistoryOutputs.Count != 0 ||
            model.Analysis.UnitSystem != "mm-N-s-C" ||
            (model.OutputFrequency != int.MinValue && model.OutputFrequency < 1))
            throw new InvalidDataException("Unexpected controlled PMX material, unit or output definition.");

        // MM_TON_S_C uses MPa, N, mm and tonne/mm³. Build in the existing
        // static deck boundary, then add the original density keyword separately.
        StringDensityConverter.SetUnit = "t/mm³";
        var density = new Density(new[] { new[] { 1d, 0d } });
        density.DensityTemp[0][0].SetEquation(model.Density[0]);
        density.DensityTemp[0][1].SetEquation(model.Density[1]);
        double massDensity = density.DensityTemp[0][0].Value;
        if (!double.IsFinite(massDensity) || massDensity <= 0 ||
            !double.IsFinite(density.DensityTemp[0][1].Value))
            throw new InvalidDataException("Expected finite positive mass density and finite temperature.");

        step.OutputFrequency = model.OutputFrequency;
        step.FieldOutputs.Clear();
        foreach (var output in model.Outputs)
        {
            if (output is null)
                throw new InvalidDataException("Null controlled field output.");
            switch (output.Type)
            {
                case "CaeModel.NodalFieldOutput":
                    step.AddFieldOutput(new NodalFieldOutput(output.Name, (NodalFieldVariable)output.Variables));
                    break;
                case "CaeModel.ElementFieldOutput":
                    step.AddFieldOutput(new ElementFieldOutput(output.Name, (ElementFieldVariable)output.Variables));
                    break;
                default:
                    throw new InvalidDataException("Unsupported controlled field output type.");
            }
        }
        MeshFiles.Measure(mesh);
        string deck = StaticAnalysisDeckWriter.Write(mesh, materials, sections, step);
        if (model.OriginalNodeExport)
        {
            int start = deck.IndexOf("*Node\n", StringComparison.Ordinal);
            int end = deck.IndexOf("*Element", start, StringComparison.OrdinalIgnoreCase);
            if (start < 0 || end <= start) throw new InvalidDataException("Original node block is missing.");
            deck = deck[..start] + CalNodeFormatting.Write3D(mesh.Nodes) + deck[end..];
        }
        int sectionOffset = deck.IndexOf("*Solid section", StringComparison.OrdinalIgnoreCase);
        if (sectionOffset <= 0 || deck[sectionOffset - 1] != '\n')
            throw new InvalidDataException("Original deck has no section boundary for the density keyword.");
        deck = deck.Insert(sectionOffset, MaterialDeckWriter.WriteDensity(density));
        deck = "*Heading\nUnit system: MM_TON_S_C\nModel space: ThreeD\n" + deck;
        return (deck, massDensity, materials[0].Name, step.Name);
    }

    private sealed record ControlledDefinition(AnalysisSpec Analysis, string[] Density, int OutputFrequency,
        CapturedOutput[] Outputs, bool OriginalNodeExport = false);
    private sealed record CapturedOutput(string Name, string Type, int Variables);
}
