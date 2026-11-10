using CaeGlobals;
using CaeJob;
using CaeMesh;
using CaeModel;
using PrePoMax;
using UserControls;

namespace PrePoMaxX.UI;

/// <summary>Drop target of a tree drag (TryGetOrderedDictionaryDropTarget): layout parent group and index.</summary>
public sealed class TreeDropTarget
{
    public string GroupId {get;init;}
    public int Index {get;init;}
    public string Position {get;init;}
}

/// <summary>
/// Port of the ordered-dictionary (tree group) rules of the original UserControls/ModelTree.cs:
/// OrderedDictionaryTreeContext per collection, tsmiCreateGroup_Click (index and GetNextGroupName /
/// GetNextPartGroupName), CheckNodeName for groups, TryGetSelectedGroupRemoval,
/// GetOrderedDictionaryItemNames, TryGetOrderedDictionaryDropTarget with GetDropPosition,
/// AdjustDropTargetIndex and IsOrderedDictionaryMoveUnchanged, and the step drop rules. Every
/// change is applied through Controller.ChangeOrderedDictionaryItemLayoutCommand / MoveStepsCommand
/// as FrmMain does.
/// </summary>
public static class OriginalTreeLayout
{
    static readonly string[] StepFamilies = ["Boundary conditions", "Loads", "Defined fields", "History outputs", "Field outputs"];

    public static ViewType View(string family) => family switch
    {
        "Geometry parts" or "Mesh setup" => ViewType.Geometry,
        _ when family.StartsWith("Result ") => ViewType.Results,
        _ => ViewType.Model,
    };

    /// <summary>The value type of the collection (the type AddObjectsToNode registers the context with).</summary>
    public static Type ItemType(string family) => family switch
    {
        "Geometry parts" or "Parts" or "Result parts" => typeof(BasePart),
        "Mesh setup" => typeof(MeshSetupItem),
        "Node sets" or "Result node sets" => typeof(FeNodeSet),
        "Element sets" or "Result element sets" => typeof(FeElementSet),
        "Surfaces" or "Result surfaces" => typeof(FeSurface),
        "Reference points" or "Result reference points" => typeof(FeReferencePoint),
        "Coordinate systems" or "Result coordinate systems" => typeof(CoordinateSystem),
        "Materials" => typeof(Material),
        "Sections" => typeof(Section),
        "Constraints" => typeof(CaeModel.Constraint),
        "Surface interactions" => typeof(SurfaceInteraction),
        "Contact pairs" => typeof(ContactPair),
        "Distributions" => typeof(Distribution),
        "Amplitudes" => typeof(Amplitude),
        "Initial conditions" => typeof(InitialCondition),
        "Jobs" => typeof(AnalysisJob),
        "Boundary conditions" => typeof(BoundaryCondition),
        "Loads" => typeof(Load),
        "Defined fields" => typeof(DefinedField),
        "History outputs" => typeof(HistoryOutput),
        "Field outputs" => typeof(FieldOutput),
        _ => null,
    };

    /// <summary>Controller.GetOrderedDictionaryItemLayout for the collection, or null when it cannot be organised.</summary>
    public static IOrderedDictionaryItemLayout<string> Dictionary(Controller controller, string family, string step)
    {
        var model = controller.Model;
        var mesh = model?.Mesh;
        var results = controller.CurrentResult?.Mesh;
        object dictionary = family switch
        {
            "Geometry parts" => model?.Geometry?.Parts,
            "Mesh setup" => model?.Geometry?.MeshSetupItems,
            "Parts" => mesh?.Parts,
            "Node sets" => mesh?.NodeSets,
            "Element sets" => mesh?.ElementSets,
            "Surfaces" => mesh?.Surfaces,
            "Reference points" => mesh?.ReferencePoints,
            "Coordinate systems" => mesh?.CoordinateSystems,
            "Materials" => model?.Materials,
            "Sections" => model?.Sections,
            "Constraints" => model?.Constraints,
            "Surface interactions" => model?.SurfaceInteractions,
            "Contact pairs" => model?.ContactPairs,
            "Distributions" => model?.Distributions,
            "Amplitudes" => model?.Amplitudes,
            "Initial conditions" => model?.InitialConditions,
            "Jobs" => controller.Jobs,
            "Result parts" => results?.Parts,
            "Result node sets" => results?.NodeSets,
            "Result element sets" => results?.ElementSets,
            "Result surfaces" => results?.Surfaces,
            "Result reference points" => results?.ReferencePoints,
            "Result coordinate systems" => results?.CoordinateSystems,
            _ when StepFamilies.Contains(family) && step != null => StepDictionary(controller.GetStep(step), family),
            _ => null,
        };
        return dictionary as IOrderedDictionaryItemLayout<string>;
    }

    static object StepDictionary(Step step, string family) => step == null ? null : family switch
    {
        "Boundary conditions" => step.BoundaryConditions,
        "Loads" => step.Loads,
        "Defined fields" => step.DefinedFields,
        "History outputs" => step.HistoryOutputs,
        "Field outputs" => step.FieldOutputs,
        _ => null,
    };

    public static bool CanOrganize(Controller controller, string family, string step) =>
        ItemType(family) != null && Dictionary(controller, family, step) != null;

    /// <summary>AddOrderedDictionaryLayoutNodes: the items in layout order with their folders.</summary>
    public static ModelTreeEntry[] Build(Controller controller, string family, string step, IEnumerable<NamedClass> items,
                                         Func<NamedClass, ModelTreeEntry> entry)
    {
        var byName = new Dictionary<string, NamedClass>(StringComparer.OrdinalIgnoreCase);
        foreach (var item in items) byName[item.Name] = item;
        var layout = Dictionary(controller, family, step);
        if (layout == null) return byName.Values.Select(entry).ToArray();
        ModelTreeEntry[] Nodes(IEnumerable<OrderedDictionaryItemNode<string>> nodes) => nodes.SelectMany(n => n.IsGroup
            ? new[] { new ModelTreeEntry { Family = family, Step = step, Name = n.Name, Group = true, FolderId = n.Id.ToString(),
                                           Children = Nodes(n.Children), Icon = "Folder.ico" } }
            : byName.TryGetValue(n.Key, out var item) ? new[] { entry(item) } : Array.Empty<ModelTreeEntry>()).ToArray();
        return Nodes(layout.GetItemLayoutSnapshot().Nodes);
    }

    static Guid? Id(string id) => string.IsNullOrEmpty(id) ? null : Guid.Parse(id);

    static OrderedDictionaryTreeLayoutChange Apply(Controller controller, OrderedDictionaryTreeLayoutChange change)
    {
        controller.ChangeOrderedDictionaryItemLayoutCommand(change);
        return change;
    }

    static IList<OrderedDictionaryItemNode<string>> Children(IEnumerable<OrderedDictionaryItemNode<string>> nodes, Guid groupId)
    {
        foreach (var node in nodes)
        {
            if (!node.IsGroup) continue;
            if (node.Id == groupId) return node.Children;
            var children = Children(node.Children, groupId);
            if (children != null) return children;
        }
        return null;
    }

    static bool FindItem(IEnumerable<OrderedDictionaryItemNode<string>> nodes, string key, IEqualityComparer<string> comparer,
                         Guid? parent, out Guid? parentId, out int index)
    {
        int i = 0;
        foreach (var node in nodes)
        {
            if (node.IsItem && comparer.Equals(node.Key, key)) { parentId = parent; index = i; return true; }
            if (node.IsGroup && FindItem(node.Children, key, comparer, node.Id, out parentId, out index)) return true;
            i++;
        }
        parentId = null;
        index = -1;
        return false;
    }

    static bool FindGroup(IEnumerable<OrderedDictionaryItemNode<string>> nodes, Guid groupId, Guid? parent,
                          out Guid? parentId, out int index)
    {
        int i = 0;
        foreach (var node in nodes)
        {
            if (node.IsGroup && node.Id == groupId) { parentId = parent; index = i; return true; }
            if (node.IsGroup && FindGroup(node.Children, groupId, node.Id, out parentId, out index)) return true;
            i++;
        }
        parentId = null;
        index = -1;
        return false;
    }

    static bool ContainsGroup(IEnumerable<OrderedDictionaryItemNode<string>> nodes, Guid groupId) =>
        nodes.Any(n => n.IsGroup && (n.Id == groupId || ContainsGroup(n.Children, groupId)));

    static bool IsDescendant(IEnumerable<OrderedDictionaryItemNode<string>> nodes, Guid groupId, Guid? possible)
    {
        if (!possible.HasValue) return false;
        foreach (var node in nodes)
        {
            if (!node.IsGroup) continue;
            if (node.Id == groupId) return ContainsGroup(node.Children, possible.Value);
            if (IsDescendant(node.Children, groupId, possible)) return true;
        }
        return false;
    }

    /// <summary>GetOrderedDictionaryItemNames: a geometry compound carries its sub parts along.</summary>
    public static string[] ItemNames(Controller controller, string family, string step, string[] names)
    {
        var dictionary = Dictionary(controller, family, step);
        var result = new List<string>();
        var added = new HashSet<string>(dictionary.Comparer);
        foreach (string name in names)
        {
            if (added.Add(name)) result.Add(name);
            if (family == "Geometry parts" && controller.Model.Geometry.Parts.TryGetValue(name, out var part) &&
                part is CompoundGeometryPart compound)
                foreach (string sub in compound.SubPartNames)
                    if (dictionary.ContainsKey(sub) && added.Add(sub)) result.Add(sub);
        }
        return result.ToArray();
    }

    static bool IsPartLayout(string family) =>
        ItemType(family) == typeof(BasePart) && View(family) != ViewType.Results;

    static string NextGroupName(IEnumerable<OrderedDictionaryItemNode<string>> nodes)
    {
        var names = new HashSet<string>(nodes.Where(n => n.IsGroup).Select(n => n.Name), StringComparer.OrdinalIgnoreCase);
        string name = "Group";
        int id = 1;
        while (names.Contains(name)) name = "Group-" + id++;
        return name;
    }

    /// <summary>tsmiCreateGroup_Click. single: the selection is one collection node (groupId null, no items)
    /// or one folder (groupId); otherwise itemNames are the selected items.</summary>
    public static string CreateGroup(Controller controller, string family, string step, bool single, string groupId, string[] itemNames)
    {
        var dictionary = Dictionary(controller, family, step) ?? throw new NotSupportedException("The selected model-tree collection cannot be organized.");
        var layout = dictionary.GetItemLayoutSnapshot();
        Guid? parent = null;
        int index;
        string[] names = null;
        if (single && groupId == null && (itemNames == null || itemNames.Length == 0)) index = layout.Nodes.Count;
        else if (single && groupId != null)
        {
            parent = Guid.Parse(groupId);
            index = Children(layout.Nodes, parent.Value).Count;
        }
        else
        {
            names = ItemNames(controller, family, step, itemNames);
            Guid? common = null;
            bool first = true, same = true;
            int firstIndex = int.MaxValue;
            foreach (string name in names)
            {
                if (!FindItem(layout.Nodes, name, dictionary.Comparer, null, out var itemParent, out int itemIndex))
                    throw new KeyNotFoundException("The item was not found in the ordered dictionary layout.");
                if (first) { common = itemParent; first = false; }
                else if (common != itemParent) same = false;
                if (itemIndex < firstIndex) firstIndex = itemIndex;
            }
            if (same) { parent = common; index = firstIndex; }
            else { parent = null; index = layout.Nodes.Count; }
        }
        string groupName = IsPartLayout(family) ? controller.GetNextPartGroupName()
            : NextGroupName(parent.HasValue ? Children(layout.Nodes, parent.Value) : layout.Nodes);
        var id = Guid.NewGuid();
        Apply(controller, OrderedDictionaryTreeLayoutChange.CreateGroup(View(family), ItemType(family), step, names, id, parent, index, groupName));
        return id.ToString();
    }

    /// <summary>CheckNodeName for a group node.</summary>
    public static bool CheckGroupName(Controller controller, string family, string step, string groupId, string newName)
    {
        if (IsPartLayout(family)) return controller.CheckPartGroupName(Guid.Parse(groupId), newName);
        var layout = Dictionary(controller, family, step).GetItemLayoutSnapshot();
        FindGroup(layout.Nodes, Guid.Parse(groupId), null, out var parent, out _);
        var siblings = parent.HasValue ? Children(layout.Nodes, parent.Value) : layout.Nodes;
        return !siblings.Any(n => n.IsGroup && n.Id != Guid.Parse(groupId) && string.Equals(n.Name, newName, StringComparison.OrdinalIgnoreCase));
    }

    public static void RenameGroup(Controller controller, string family, string step, string groupId, string newName) =>
        Apply(controller, OrderedDictionaryTreeLayoutChange.RenameGroup(View(family), ItemType(family), step, Guid.Parse(groupId), newName));

    /// <summary>TryGetSelectedGroupRemoval: the folders are removed, their items move to the parent.</summary>
    public static void RemoveGroups(Controller controller, string family, string step, string[] groupIds) =>
        Apply(controller, OrderedDictionaryTreeLayoutChange.RemoveGroups(View(family), ItemType(family), step, groupIds.Select(Guid.Parse).ToArray()));

    /// <summary>GetDropPosition: top and bottom band insert before/after, the middle drops into a group.</summary>
    public static string DropPosition(double fraction, bool canDropInto)
    {
        if (!canDropInto) return fraction < 0.5 ? "Before" : "After";
        if (fraction < 0.25) return "Before";
        if (fraction >= 0.75) return "After";
        return "Into";
    }

    /// <summary>TryGetOrderedDictionaryDropTarget. targetKind: "Root" (the collection node), "Group" (target = folder id)
    /// or "Item" (target = item name). Dragged: itemNames, or draggedGroupId for a single folder.</summary>
    public static TreeDropTarget DropTarget(Controller controller, string family, string step, string[] itemNames, string draggedGroupId,
                                            string targetKind, string target, double fraction)
    {
        var dictionary = Dictionary(controller, family, step);
        if (dictionary == null) return null;
        var layout = dictionary.GetItemLayoutSnapshot();
        string position = "Into";
        Guid? targetGroup = null;
        int targetIndex;
        if (targetKind == "Root") targetIndex = layout.Nodes.Count;
        else if (targetKind == "Group")
        {
            position = DropPosition(fraction, true);
            var id = Guid.Parse(target);
            if (position == "Into") { targetGroup = id; targetIndex = Children(layout.Nodes, id).Count; }
            else
            {
                if (!FindGroup(layout.Nodes, id, null, out targetGroup, out targetIndex)) return null;
                if (position == "After") targetIndex++;
            }
        }
        else if (targetKind == "Item" && dictionary.ContainsKey(target))
        {
            position = DropPosition(fraction, false);
            if (!FindItem(layout.Nodes, target, dictionary.Comparer, null, out targetGroup, out targetIndex)) return null;
            if (position == "After") targetIndex++;
        }
        else return null;
        Guid? dragged = Id(draggedGroupId);
        if (dragged.HasValue && (targetGroup == dragged || IsDescendant(layout.Nodes, dragged.Value, targetGroup))) return null;
        // AdjustDropTargetIndex
        int before = 0;
        if (dragged.HasValue)
        {
            FindGroup(layout.Nodes, dragged.Value, null, out var parent, out int index);
            if (parent == targetGroup && index < targetIndex) before++;
        }
        else
            foreach (string key in itemNames)
            {
                FindItem(layout.Nodes, key, dictionary.Comparer, null, out var parent, out int index);
                if (parent == targetGroup && index < targetIndex) before++;
            }
        targetIndex -= before;
        if (targetIndex < 0) return null;
        // IsOrderedDictionaryMoveUnchanged
        var children = targetGroup.HasValue ? Children(layout.Nodes, targetGroup.Value) : layout.Nodes;
        if (children != null)
        {
            var moved = dragged.HasValue
                ? children.Where(n => n.IsGroup && n.Id == dragged.Value).ToList()
                : children.Where(n => n.IsItem && itemNames.Contains(n.Key, dictionary.Comparer)).ToList();
            int expected = dragged.HasValue ? 1 : itemNames.Distinct(dictionary.Comparer).Count();
            if (moved.Count == expected)
            {
                var remaining = children.Where(n => !moved.Contains(n)).ToList();
                if (targetIndex <= remaining.Count)
                {
                    remaining.InsertRange(targetIndex, moved);
                    if (children.SequenceEqual(remaining)) return null;
                }
            }
        }
        return new TreeDropTarget { GroupId = targetGroup?.ToString(), Index = targetIndex, Position = position };
    }

    /// <summary>cltv_DragDrop: MoveItems or MoveGroup through the controller.</summary>
    public static void Drop(Controller controller, string family, string step, string[] itemNames, string draggedGroupId, TreeDropTarget target)
    {
        Guid? group = Id(target.GroupId);
        Apply(controller, draggedGroupId != null
            ? OrderedDictionaryTreeLayoutChange.MoveGroup(View(family), ItemType(family), step, Guid.Parse(draggedGroupId), group, target.Index)
            : OrderedDictionaryTreeLayoutChange.MoveItems(View(family), ItemType(family), step, itemNames, group, target.Index));
    }

    /// <summary>TryGetStepDropTarget with IsStepMoveUnchanged: -1 when the drop is not allowed.</summary>
    public static int StepDropIndex(Controller controller, string[] stepNames, string targetStep, double fraction)
    {
        var all = controller.GetStepNames().ToList();
        int targetIndex;
        if (targetStep == null) targetIndex = all.Count;
        else
        {
            targetIndex = all.IndexOf(targetStep);
            if (targetIndex < 0) return -1;
            if (DropPosition(fraction, false) == "After") targetIndex++;
        }
        int drop = targetIndex;
        targetIndex -= stepNames.Count(name => all.IndexOf(name) < drop);
        if (targetIndex < 0) return -1;
        var moved = all.Where(stepNames.Contains).ToList();
        var remaining = all.Where(n => !stepNames.Contains(n)).ToList();
        if (targetIndex > remaining.Count) return -1;
        remaining.InsertRange(targetIndex, moved);
        return all.SequenceEqual(remaining) ? -1 : targetIndex;
    }
}
