using System.Formats.Nrbf;

internal static partial class StaticGraph
{
    internal sealed record EditMember(string Role, int Offset, int Length, int Kind,
        int RecordId, string Value, int MaximumId);

    private static object LocatePropertySlots(SerializationRecord root,
        IEnumerable<SerializationRecord> records, byte[] graph)
    {
        var model = Record(Controller(root).GetRawValue("_model"), "CaeModel.FeModel");
        var material = Named(Entries(model, "_materials").Single(), "CaeModel.Material");
        var properties = List(material.GetRawValue("_properties")).Select(value => Record(value)).ToArray();
        var elastic = properties.Single(item => item.TypeName.FullName == "CaeModel.Elastic");
        var density = properties.Single(item => item.TypeName.FullName == "CaeModel.Density");
        ClassRecord Cell(ClassRecord property, string field, int column)
        {
            var rows = (ArrayRecord[])BoundedArray(property.GetRawValue(field), 1)
                .GetArray(typeof(CaeGlobals.EquationContainer[][]), allowNulls: false);
            return Record(Records(rows.Single())[column], "CaeGlobals.EquationContainer");
        }
        var step = Record(List(Record(model.GetRawValue("_stepCollection"), "CaeModel.StepCollection")
            .GetRawValue("_steps")).Single(), "CaeModel.StaticStep");
        var load = Named(Entries(step, "_loads").Single(), "CaeModel.CLoad");
        var owners = new[] {
            (Role: "modulus", Owner: Cell(elastic, "_youngsPoissonsTemp", 0)),
            (Role: "poisson", Owner: Cell(elastic, "_youngsPoissonsTemp", 1)),
            (Role: "density", Owner: Cell(density, "_densityTemp", 0)),
            (Role: "force", Owner: Record(load.GetRawValue("_f1"), "CaeGlobals.EquationContainer")),
            (Role: "force2", Owner: Record(load.GetRawValue("_f2"), "CaeGlobals.EquationContainer")),
            (Role: "force3", Owner: Record(load.GetRawValue("_f3"), "CaeGlobals.EquationContainer")),
            (Role: "magnitude", Owner: Record(load.GetRawValue("_magnitude"), "CaeGlobals.EquationContainer"))
        };
        RequireExclusiveRecords(records, density);
        RequireExclusiveRecords(records, owners.Select(item => item.Owner).ToArray());
        var wire = new NrbfWire(graph);
        return owners.Select(item => {
            if (item.Owner.GetBoolean("_constant")) throw new InvalidDataException("Constant equation storage is unsupported.");
            return StringSlot(wire, item.Owner, "_equation", item.Role);
        }).ToArray();
    }

    private static EditMember StringSlot(NrbfWire wire, ClassRecord owner, string field, string role)
    {
        string value = owner.GetString(field) ?? throw new InvalidDataException("Missing editable string.");
        if (value.Length is < 1 or > 4096) throw new InvalidDataException("Editable string length limit exceeded.");
        var slot = wire.StringMember(owner, field);
        return new EditMember(role, slot.Offset, slot.Length, slot.Kind, slot.Id, value, wire.MaximumId);
    }
}
