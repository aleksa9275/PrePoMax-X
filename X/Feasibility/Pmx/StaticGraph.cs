using System.Formats.Nrbf;

internal static partial class StaticGraph
{
    private const int CollectionLimit = 4096;

    internal static object ValidateEditContract(SerializationRecord root,
        IEnumerable<SerializationRecord> records, byte[] graph, bool cadModel = false, string? editScope = null)
    {
        var slots = RootSlots(root);
        var controller = Record(slots[0], "PrePoMax.Controller");
        var history = Record(controller.GetRawValue("_commands"), "PrePoMax.Commands.CommandsCollection");
        if (cadModel) ValidateCadHistory(root);
        if (!cadModel && (List(history.GetRawValue("_commands")).Length != 0 || history.GetInt32("_currPositionIndex") != -1))
            throw new InvalidDataException("The static edit requires an empty command history.");
        ReadCommandHistory(root); // Check the saved Controller back-reference.
        RequireEmptyDictionary(Record(slots[1]), "analysis jobs");
        var model = Record(controller.GetRawValue("_model"), "CaeModel.FeModel");
        var properties = Record(model.GetRawValue("_properties"), "CaeModel.ModelProperties");
        if (EnumValue(properties, "ModelSpace", "CaeModel.ModelSpaceEnum") != 1 ||
            EnumValue(properties, "ModelType", "CaeModel.ModelType") != 0 ||
            properties.GetString("GlobalResultsFileName") != null)
            throw new InvalidDataException("The static edit requires a general 3D model.");
        EmptyDictionaries(model, "_amplitudes", "_constraints", "_contactPairs", "_distributions",
            "_initialConditions", "_surfaceInteractions", "_userViews");
        if (model.HasMember("_materialOrientations"))
            EmptyDictionaries(model, "_materialOrientations");
        bool noOverrides = cadModel && model.GetRawValue("_calculixKeywordOverrides") == null ||
            Record(model.GetRawValue("_calculixKeywordOverrides")).GetInt32("_size") == 0;
        bool noUserKeywords = cadModel && model.GetRawValue("_calculixUserKeywords") == null ||
            Record(Record(model.GetRawValue("_calculixUserKeywords")).GetRawValue("_list")).GetInt32("_size") == 0;
        if (!noOverrides || !noUserKeywords)
            throw new InvalidDataException("The static edit refuses custom CalculiX keywords.");
        var parameters = Record(model.GetRawValue("_parameters"), "CaeModel.EquationParameterCollection");
        EmptyDictionaries(parameters, "_parameters", "_overriddenParameters");

        var mesh = Record(model.GetRawValue("_mesh"), "CaeMesh.FeMesh");
        var geometry = Record(model.GetRawValue("_geometry"), "CaeMesh.FeMesh");
        if (cadModel) ValidateCadGeometry(root);
        else EmptyDictionaries(geometry, "_parts", "_meshSetupItems");
        EmptyDictionaries(mesh, "_coordinateSystems", "_referencePoints", "_surfaces", "_meshSetupItems");
        foreach (var item in Entries(mesh, "_parts"))
        {
            var part = Named(item, "CaeMesh.MeshPart");
            Active(part);
            if (cadModel ? EnumValue(part, "_linearTetraType", "CaeMesh.FeElementTypeLinearTetra") != 10 :
                EnumValue(part, "_linearHexaType", "CaeMesh.FeElementTypeLinearHexa") != 10)
                throw new InvalidDataException("The static edit requires full-integration C3D8 parts.");
        }

        var material = Named(Entries(model, "_materials").Single(), "CaeModel.Material");
        var section = Named(Entries(model, "_sections").Single(), "CaeModel.SolidSection");
        Active(material);
        Active(section);
        Assignment(section);
        var steps = Record(model.GetRawValue("_stepCollection"), "CaeModel.StepCollection");
        var step = Record(List(steps.GetRawValue("_steps")).Single(), "CaeModel.StaticStep");
        Active(step);
        if (steps.GetBoolean("_onlyCheckModel") || step.GetBoolean("_direct"))
            throw new InvalidDataException("The static edit requires an ordinary automatic solve.");
        EmptyDictionaries(step, "_definedFields", "_historyOutputs");
        if (List(Record(step.GetRawValue("_stepControls"), "CaeModel.StepControls")
                .GetRawValue("_parameters")).Length != 0)
            throw new InvalidDataException("The static edit refuses custom step controls.");

        foreach (var item in Entries(step, "_boundaryConditions"))
        {
            var support = Named(item, "CaeModel.DisplacementRotation");
            CheckLoadOrSupport(support);
            if (support.GetString("_distributionName") != "Constant")
                throw new InvalidDataException("The static edit requires constant supports.");
        }
        var load = Named(Entries(step, "_loads").Single(), "CaeModel.CLoad");
        CheckLoadOrSupport(load);
        foreach (var item in Entries(step, "_fieldOutputs"))
        {
            var output = item.Value;
            Active(output);
            if (output.GetBoolean("_lastIterations") || output.GetBoolean("_contactElements") ||
                !output.GetBoolean("_global") ||
                (output.TypeName.FullName == "CaeModel.ElementFieldOutput" &&
                 EnumValue(output, "_output", "CaeModel.ElementFieldOutputOutputEnum") != 0))
                throw new InvalidDataException("The static edit requires ordinary global field outputs.");
        }
        var elastic = List(material.GetRawValue("_properties")).Select(item => Record(item))
            .Single(item => item.TypeName.FullName == "CaeModel.Elastic");
        RequireExclusiveRecords(records, model, material, elastic, section, step, load);
        if (editScope != null) return LocatePropertySlots(root, records, graph);
        return LocateEditStrings(root, records, graph);
    }

    private static void EmptyDictionaries(ClassRecord owner, params string[] fields)
    {
        foreach (string field in fields)
            RequireEmptyDictionary(Record(owner.GetRawValue(field)), field);
    }

    private static void RequireEmptyDictionary(ClassRecord ordered, string name)
    {
        var dictionary = Record(ordered.GetRawValue("_dictionary"));
        if (Record(ordered.GetRawValue("_list")).GetInt32("_size") != 0 ||
            (dictionary.HasMember("KeyValuePairs") &&
             BoundedArray(dictionary.GetRawValue("KeyValuePairs"), CollectionLimit).Lengths[0] != 0))
            throw new InvalidDataException($"The static edit does not support nonempty {name}.");
    }

    private static void Active(ClassRecord record)
    {
        if (!record.GetBoolean("_active") || !record.GetBoolean("_valid"))
            throw new InvalidDataException("The static edit requires active, valid engineering objects.");
    }

    private static void Assignment(ClassRecord record)
    {
        if (record.GetBoolean("_twoD") || record.GetRawValue("_creationData") != null ||
            (record.GetRawValue("_creationIds") is ArrayRecord ids && ids.Lengths[0] != 0))
            throw new InvalidDataException("The static edit requires direct 3D named-set assignments.");
    }

    private static void CheckLoadOrSupport(ClassRecord record)
    {
        Active(record);
        Assignment(record);
        if (record.GetBoolean("_complex") || (record.GetString("_amplitudeName") ?? "Default") != "Default" ||
            (record.GetString("_coordinateSystemName") ?? "Global") != "Global")
            throw new InvalidDataException("The static edit requires real, global loads and supports with default amplitude.");
    }

    internal static object LocateEditStrings(SerializationRecord root,
        IEnumerable<SerializationRecord> records, byte[] graph)
    {
        var model = Record(Controller(root).GetRawValue("_model"), "CaeModel.FeModel");
        var material = Named(Entries(model, "_materials").Single(), "CaeModel.Material");
        var elastic = List(material.GetRawValue("_properties")).Select(item => Record(item))
            .Single(item => item.TypeName.FullName == "CaeModel.Elastic");
        var rows = (ArrayRecord[])BoundedArray(elastic.GetRawValue("_youngsPoissonsTemp"), 1)
            .GetArray(typeof(CaeGlobals.EquationContainer[][]), allowNulls: false);
        var modulus = Record(Records(rows.Single())[0], "CaeGlobals.EquationContainer");
        var step = Record(List(Record(model.GetRawValue("_stepCollection"), "CaeModel.StepCollection")
            .GetRawValue("_steps")).Single(), "CaeModel.StaticStep");
        var load = Named(Entries(step, "_loads").Single(), "CaeModel.CLoad");
        if (Equation(load.GetRawValue("_f2")) != "0 N" || Equation(load.GetRawValue("_f3")) != "0 N")
            throw new InvalidDataException("Expected a load with no transverse components.");
        var force = Record(load.GetRawValue("_f1"), "CaeGlobals.EquationContainer");
        var magnitude = Record(load.GetRawValue("_magnitude"), "CaeGlobals.EquationContainer");

        RequireExclusiveRecords(records, modulus, force, magnitude);
        var targets = new[]
        {
            EditString.Find(graph, modulus, "modulus"),
            EditString.Find(graph, force, "force"),
            EditString.Find(graph, magnitude, "magnitude")
        };
        if (targets.Select(target => target.RecordId).Distinct().Count() != targets.Length ||
            targets[1].Value != targets[2].Value)
            throw new InvalidDataException("Expected distinct edit records and matching positive axial force and magnitude.");
        return targets;
    }

    private static void RequireExclusiveRecords(IEnumerable<SerializationRecord> records,
        params ClassRecord[] owners)
    {
        var uses = new Dictionary<SerializationRecordId, int>();
        foreach (var owner in owners)
            if (!uses.TryAdd(owner.Id, 0))
                throw new InvalidDataException("Multiple edit roles share an owning record.");

        void Count(object? value)
        {
            if (value is SerializationRecord record && uses.TryGetValue(record.Id, out int count))
                uses[record.Id] = count + 1;
        }

        int arraySlots = 0;
        foreach (var record in records)
        {
            if (record is ClassRecord item)
            {
                foreach (string member in item.MemberNames)
                    Count(item.GetRawValue(member));
            }
            else if (record is SZArrayRecord<SerializationRecord> items)
            {
                arraySlots += BoundedArray(items, CollectionLimit).Lengths[0];
                if (arraySlots > 100_000)
                    throw new InvalidDataException("Equation ownership array audit exceeds the slot limit.");
                foreach (var value in items.GetArray())
                    Count(value);
            }
            else if (record is ArrayRecord array && !CannotContainEquation(array))
            {
                throw new InvalidDataException("Unsupported array layout for equation ownership audit.");
            }
        }
        if (uses.Values.Any(count => count != 1))
            throw new InvalidDataException("An edit graph record does not have exactly one owner.");
    }

    private static bool CannotContainEquation(ArrayRecord array)
    {
        var element = array.TypeName.GetElementType();
        return element.IsArray || element.FullName is
            "System.Boolean" or "System.Byte" or "System.SByte" or "System.Char" or
            "System.Int16" or "System.UInt16" or "System.Int32" or "System.UInt32" or
            "System.Int64" or "System.UInt64" or "System.Single" or "System.Double" or
            "System.Decimal" or "System.DateTime" or "System.TimeSpan" or "System.String";
    }

    public static object Read(SerializationRecord root)
    {
        var controller = Controller(root);
        var model = Record(controller.GetRawValue("_model"), "CaeModel.FeModel");
        var mesh = Record(model.GetRawValue("_mesh"), "CaeMesh.FeMesh");
        var geometry = Record(model.GetRawValue("_geometry"), "CaeMesh.FeMesh");
        if (mesh.Id.Equals(geometry.Id))
            throw new InvalidDataException("Geometry and analysis mesh share a record.");
        var units = Record(model.GetRawValue("_unitSystem"), "CaeGlobals.UnitSystem");
        int unitValue = EnumValue(units, "_unitSystemType", "CaeGlobals.UnitSystemType");
        if (unitValue != 2)
            throw new InvalidDataException("This probe supports MM_TON_S_C model units.");

        return new
        {
            unitSystem = "MM_TON_S_C",
            nodeSets = Sets(mesh, "_nodeSets", "CaeMesh.FeNodeSet"),
            elementSets = Sets(mesh, "_elementSets", "CaeMesh.FeElementSet"),
            parts = Entries(mesh, "_parts").Select(pair =>
            {
                var part = Named(pair, "CaeMesh.MeshPart");
                return new { name = pair.Key, id = part.GetInt32("_partId"),
                    nodes = Labels(part, "_nodeLabels"), elements = Labels(part, "_labels") };
            }).ToArray(),
            materials = Entries(model, "_materials").Select(Material).ToArray(),
            sections = Entries(model, "_sections").Select(pair =>
            {
                var section = Named(pair, "CaeModel.SolidSection");
                return new { name = pair.Key, material = section.GetString("_materialName"),
                    region = section.GetString("_regionName"),
                    regionType = EnumValue(section, "_regionType", "CaeGlobals.RegionTypeEnum") };
            }).ToArray(),
            steps = List(Record(model.GetRawValue("_stepCollection"), "CaeModel.StepCollection")
                .GetRawValue("_steps")).Select(Step).ToArray()
        };
    }

    public static object ReadCommandHistory(SerializationRecord root)
    {
        var controller = Controller(root);
        var history = Record(controller.GetRawValue("_commands"), "PrePoMax.Commands.CommandsCollection");
        var owner = Record(history.GetRawValue("_controller"), "PrePoMax.Controller");
        if (!owner.Id.Equals(controller.Id))
            throw new InvalidDataException("Command history points to a different controller.");

        var commands = List(history.GetRawValue("_commands"));
        int cursor = history.GetInt32("_currPositionIndex");
        if (cursor < -1 || cursor >= commands.Length)
            throw new InvalidDataException("Command history cursor is out of range.");

        var ordinals = new Dictionary<SerializationRecordId, int>();
        return new
        {
            cursor,
            appliedRecordCount = cursor + 1,
            remainingRecordCount = commands.Length - cursor - 1,
            commands = commands.Select(item =>
            {
                var command = Record(item);
                string type = command.TypeName.FullName;
                if (!type.StartsWith("PrePoMax.Commands.", StringComparison.Ordinal))
                    throw new InvalidDataException("Unexpected command record type.");
                if (!ordinals.TryGetValue(command.Id, out int ordinal))
                {
                    ordinal = ordinals.Count;
                    ordinals.Add(command.Id, ordinal);
                }
                return new { type, ordinal };
            }).ToArray()
        };
    }

    private static ClassRecord Controller(SerializationRecord root)
        => Record(RootSlots(root)[0], "PrePoMax.Controller");

    private static object?[] RootSlots(SerializationRecord root)
    {
        var slots = (object?[])BoundedArray(root, 4).GetArray(typeof(object[]));
        if (slots.Length is not (3 or 4))
            throw new InvalidDataException("Unexpected PMX root layout.");
        return slots;
    }

    private static object Material(KeyValuePair<string, ClassRecord> pair)
    {
        var material = Named(pair, "CaeModel.Material");
        return new
        {
            name = pair.Key,
            temperatureDependent = material.GetBoolean("_temperatureDependent"),
            properties = List(material.GetRawValue("_properties")).Select(property =>
            {
                var record = Record(property);
                string type = record.TypeName.FullName;
                string field = type switch
                {
                    "CaeModel.Elastic" => "_youngsPoissonsTemp",
                    "CaeModel.Density" => "_densityTemp",
                    _ => throw new InvalidDataException("Unsupported material property.")
                };
                return new { type, rows = EquationRows(record.GetRawValue(field)).ToArray() };
            }).ToArray()
        };
    }

    private static object Step(object? value)
    {
        var step = Record(value, "CaeModel.StaticStep");
        return new
        {
            name = step.GetString("_name"),
            nonlinearGeometry = step.GetBoolean("_nlgeom"),
            perturbation = step.GetBoolean("_perturbation"),
            runAnalysis = step.GetBoolean("_runAnalysis"),
            solverType = EnumValue(step, "_solverType", "CaeModel.SolverTypeEnum"),
            incrementationType = EnumValue(step, "_incrementationType", "CaeModel.IncrementationTypeEnum"),
            timePeriod = step.GetDouble("_timePeriod"),
            initialTimeIncrement = step.GetDouble("_initialTimeIncrement"),
            minTimeIncrement = step.GetDouble("_minTimeIncrement"),
            maxTimeIncrement = step.GetDouble("_maxTimeIncrement"),
            maxIncrements = step.GetInt32("_maxIncrements"),
            outputFrequency = step.GetInt32("_outputFrequency"),
            fieldOutputs = Entries(step, "_fieldOutputs").Select(pair =>
            {
                var field = Named(pair, pair.Value.TypeName.FullName);
                string type = field.TypeName.FullName;
                string variableType = type switch
                {
                    "CaeModel.NodalFieldOutput" => "CaeModel.NodalFieldVariable",
                    "CaeModel.ElementFieldOutput" => "CaeModel.ElementFieldVariable",
                    _ => throw new InvalidDataException("Unsupported field output.")
                };
                return new { name = pair.Key, type,
                    variables = EnumValue(field, "_variables", variableType) };
            }).ToArray(),
            historyOutputCount = Entries(step, "_historyOutputs").Count(),
            constraints = Entries(step, "_boundaryConditions").Select(pair =>
            {
                var condition = Named(pair, "CaeModel.DisplacementRotation");
                return new { name = pair.Key, region = condition.GetString("_regionName"),
                    regionType = EnumValue(condition, "_regionType", "CaeGlobals.RegionTypeEnum"),
                    displacements = Equations(condition, "_u1", "_u2", "_u3"),
                    rotations = Equations(condition, "_ur1", "_ur2", "_ur3") };
            }).ToArray(),
            loads = Entries(step, "_loads").Select(pair =>
            {
                var load = Named(pair, "CaeModel.CLoad");
                return new { name = pair.Key, region = load.GetString("_regionName"),
                    regionType = EnumValue(load, "_regionType", "CaeGlobals.RegionTypeEnum"),
                    force = Equations(load, "_f1", "_f2", "_f3") };
            }).ToArray()
        };
    }

    private static string?[][] EquationRows(object? value)
    {
        var outer = BoundedArray(value, 256);
        var rows = (ArrayRecord[])outer.GetArray(typeof(CaeGlobals.EquationContainer[][]), allowNulls: false);
        foreach (var row in rows)
            BoundedArray(row, 3);
        return rows.Select(row => Records(row).Select(Equation).ToArray()).ToArray();
    }

    private static string?[] Equations(ClassRecord owner, params string[] fields) =>
        fields.Select(field => Equation(owner.GetRawValue(field))).ToArray();

    private static string? Equation(object? value)
    {
        string? equation = Record(value, "CaeGlobals.EquationContainer").GetString("_equation");
        if (equation?.Length > 4096)
            throw new InvalidDataException("Equation text exceeds the probe limit.");
        return equation;
    }

    private static int EnumValue(ClassRecord owner, string field, string type) =>
        Record(owner.GetRawValue(field), type).GetInt32("value__");

    private static Dictionary<string, int[]> Sets(ClassRecord mesh, string field, string type) =>
        Entries(mesh, field).ToDictionary(pair => pair.Key, pair => Labels(Named(pair, type), "_labels"),
            StringComparer.Ordinal);

    private static int[] Labels(ClassRecord record, string field)
    {
        var values = (int[])BoundedArray(record.GetRawValue(field), 250_000).GetArray(typeof(int[]));
        if (values.Any(id => id < 1) || values.Distinct().Count() != values.Length)
            throw new InvalidDataException("Invalid group labels.");
        return values;
    }

    private static ClassRecord Named(KeyValuePair<string, ClassRecord> pair, string type)
    {
        var record = Record(pair.Value, type);
        if (record.GetString("_name") != pair.Key)
            throw new InvalidDataException("A collection key differs from the object name.");
        return record;
    }

    private static IEnumerable<KeyValuePair<string, ClassRecord>> Entries(ClassRecord owner, string field)
    {
        var ordered = Record(owner.GetRawValue(field));
        var dictionary = Record(ordered.GetRawValue("_dictionary"));
        var entries = new Dictionary<string, ClassRecord>(StringComparer.Ordinal);
        if (dictionary.MemberNames.Contains("KeyValuePairs"))
        {
            foreach (object? item in Records(dictionary.GetRawValue("KeyValuePairs")))
            {
                var pair = Record(item);
                string key = pair.GetString("key") ?? throw new InvalidDataException("Missing collection key.");
                if (!entries.TryAdd(key, Record(pair.GetRawValue("value"))))
                    throw new InvalidDataException("Duplicate collection key.");
            }
        }

        var keys = List(ordered.GetRawValue("_list"));
        if (keys.Length != entries.Count)
            throw new InvalidDataException("Dictionary keys do not match the ordered list.");
        foreach (object? item in keys)
        {
            if (item is not string key || !entries.Remove(key, out var value))
                throw new InvalidDataException("Invalid ordered dictionary key.");
            yield return new(key, value);
        }
    }

    private static object?[] List(object? value)
    {
        var list = Record(value);
        int size = list.GetInt32("_size");
        object?[] items = Records(list.GetRawValue("_items"));
        if (size < 0 || size > items.Length)
            throw new InvalidDataException("Invalid serialized list size.");
        return items[..size];
    }

    private static object?[] Records(object? value)
    {
        var array = BoundedArray(value, CollectionLimit);
        if (array is SZArrayRecord<string> strings)
            return strings.GetArray();
        if (array is SZArrayRecord<SerializationRecord> records)
            return records.GetArray();
        throw new InvalidDataException($"Unsupported record array {array.TypeName.FullName}.");
    }

    private static ArrayRecord BoundedArray(object? value, int limit)
    {
        if (value is not ArrayRecord array || array.Rank != 1 || array.Lengths[0] > limit)
            throw new InvalidDataException("Unexpected record array rank or size.");
        return array;
    }

    private static ClassRecord Record(object? value, string? type = null)
    {
        if (value is not ClassRecord record || (type != null && record.TypeName.FullName != type))
            throw new InvalidDataException($"Expected {type ?? "a class record"}.");
        return record;
    }
}
