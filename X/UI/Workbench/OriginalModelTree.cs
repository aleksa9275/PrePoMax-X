using CaeGlobals;
using CaeJob;
using CaeMesh;
using CaeModel;
using CaeResults;
using PrePoMax;

namespace PrePoMaxX.UI;

/// <summary>
/// Port of the item rules of the original UserControls/ModelTree.cs: AppendMenuFields with
/// CanCreate/CanDuplicate/CanPropagate/CanPreview/CanSearchContactPairs/CanSwapMergeMasterSlave/
/// CanHide/CanDeactivate, SetNodeStatus/SetSplitSubPartNodeStatus and the node texts
/// (UpdateNumberOfStepControls). The WinForms tree is not portable; the rules are kept here
/// verbatim in intent and order so that model_tree.py can apply PrepareToolStripItem.
/// </summary>
public static class OriginalModelTree
{
    public const string Geometry = "Geometry", Model = "Model", Results = "Results";

    /// <summary>ModelTree.CanCreate for a static node of the given tree.</summary>
    public static bool CanCreate(string nodeName, string view) => nodeName switch
    {
        "Mesh Setup" => true,
        "Node Sets" or "Element Sets" or "Surfaces" => view == Model,
        "Reference Points" or "Coordinate Systems" or "Materials" or "Sections" or "Constraints" or
        "Surface Interactions" or "Contact Pairs" or "Distributions" or "Amplitudes" or "Initial Conditions" or
        "Steps" or "History Outputs" or "BCs" or "Loads" or "Defined Fields" or "Analyses" => true,
        "Field Outputs" => view == Model || view == Results,
        _ => false,
    };

    /// <summary>AppendMenuFields for a static (group) node.</summary>
    public static string[] GroupFields(string nodeName, string view)
    {
        var fields = new List<string>();
        if (view == Model && nodeName == "Model") return ["Edit", "EditCalculixKeywords"];
        if (CanCreate(nodeName, view)) fields.Add("Create");
        if (view == Model && nodeName == "Materials") fields.Add("MaterialLibrary");
        if (view == Model && (nodeName == "Constraints" || nodeName == "Contact Pairs")) fields.Add("SearchContactPairs");
        return fields.ToArray();
    }

    static bool CanDuplicate(NamedClass item, string view) =>
        view == Geometry && item is MeshSetupItem ||
        view == Model && (item is FeNodeSet || item is FeElementSet || item is FeSurface || item is FeReferencePoint || item is CoordinateSystem) ||
        item is Material || item is Section || item is Constraint || item is SurfaceInteraction || item is ContactPair ||
        item is Distribution || item is Amplitude || item is InitialCondition || item is Step || item is HistoryOutput ||
        item is FieldOutput || item is BoundaryCondition || item is Load || item is DefinedField || item is AnalysisJob ||
        view == Results && (item is FeReferencePoint || item is CoordinateSystem || item is ResultFieldOutput || item is ResultHistoryOutput);

    static bool CanPropagate(NamedClass item) =>
        item is HistoryOutput || item is FieldOutput || item is BoundaryCondition || item is Load || item is DefinedField;

    static bool CanSwapMergeMasterSlave(NamedClass item) => item is Tie || item is Joint || item is ContactPair;

    public static bool CanHide(NamedClass item) =>
        item is BasePart || item is FeReferencePoint || item is CoordinateSystem || item is Constraint || item is ContactPair ||
        item is InitialCondition || item is BoundaryCondition || item is Load || item is DefinedField;

    static bool CanDeactivate(NamedClass item) =>
        item is MeshSetupItem || item is MeshPart || item is Material || item is Constraint || item is ContactPair ||
        item is InitialCondition || item is Step || item is HistoryOutput || item is FieldOutput || item is BoundaryCondition ||
        item is Load || item is DefinedField;

    /// <summary>AppendMenuFields for an item node.</summary>
    public static string[] ItemFields(NamedClass item, string view, bool subPart)
    {
        var f = new List<string>();
        bool resultSet = view == Results && (item is FeNodeSet || item is FeElementSet || item is FeSurface);
        if (!(item is Field || item is HistoryResultSet || item is HistoryResultField) && !resultSet) f.Add("Edit");
        if (item is Step) f.Add("EditStepControls");
        if (item is BasePart) f.Add("Query");
        if (CanDuplicate(item, view)) f.Add("Duplicate");
        if (CanPropagate(item)) f.Add("Propagate");
        if (item is IPreviewable) f.Add("Preview");
        if (item is HistoryResultData || item is Amplitude) f.Add("AddToPlot");
        if (item is GeometryPart && view == Geometry)
        {
            f.Add("CompoundPart");
            f.Add("SwapParts");
            if (!subPart)
            {
                f.Add("MeshingParameters");
                f.Add("PreviewEdgeMesh");
                f.Add("CreateMesh");
            }
            f.Add("CopyPartToGeometry");
        }
        if (item is MeshSetupItem && view == Geometry) f.Add("CreateMesh");
        if (item is MeshPart && view == Model) f.Add("MergePart");
        if (item is ResultPart && view == Results) f.Add("MergePart");
        if (item is FeElementSet && view == Model) f.Add("ConvertToPart");
        if (CanSwapMergeMasterSlave(item)) f.Add("SwapMergeMasterSlave");
        if (CanHide(item)) f.Add(item.Visible ? "Hide" : "Show");
        if (item is BasePart) f.Add("ColorTransparency");
        if (item is ResultPart resultPart && ResultPart.ResultRepresentationAvailable)
            f.Add(resultPart.ResultRepresentation ? "ResultRepresentationOn" : "ResultRepresentationOff");
        if (item is AnalysisJob) f.AddRange(["Run", "Monitor", "Results", "Kill"]);
        if (CanDeactivate(item)) f.Add(item.Active ? "Deactivate" : "Activate");
        if (!resultSet) f.Add("Delete");
        return f.ToArray();
    }

    /// <summary>SetNodeStatus: image key, gray fore colour and invalid (error) colour.</summary>
    public static void Status(ModelTreeEntry entry, NamedClass item, Controller controller)
    {
        entry.Icon = "Dots.ico";
        if (item.Active)
        {
            if (item is AnalysisJob job)
            {
                entry.Icon = job.JobStatus switch
                {
                    JobStatus.OK => "OK.ico",
                    JobStatus.Running => "Running.ico",
                    JobStatus.FailedWithResults => "Warning.ico",
                    _ => "NoResult.ico",
                };
            }
            else if (CanHide(item) && !item.Visible)
            {
                entry.Gray = true;
                entry.Icon = "Hide.ico";
            }
            else
            {
                if (item is BasePart part)
                {
                    PartType partType = part.PartType;
                    if (part is CompoundGeometryPart compound && compound.GetSingleSplitSubPartName() != null &&
                        entry.Children.Length > 0 && entry.Children[0].Item is BasePart cell)
                        partType = cell.PartType;
                    string transparent = part.Color.A == 255 ? "" : "_transparent";
                    entry.Icon = partType switch
                    {
                        PartType.Solid or PartType.SolidAsShell => "Solid" + transparent + ".ico",
                        PartType.Shell => "Shell" + transparent + ".ico",
                        PartType.Wire => "Wire" + transparent + ".ico",
                        PartType.Compound => "Compound" + transparent + ".ico",
                        _ => entry.Icon,
                    };
                    if (part is GeometryPart && controller.HasSmallFeatures(part.Name)) entry.Icon = SmallFeatures(entry.Icon);
                }
                else if (item is Step) entry.Icon = "Step.ico";
                if (item is GeometryPart geometryPart &&
                    (geometryPart.PartType == PartType.Solid || geometryPart.PartType == PartType.SolidAsShell) &&
                    geometryPart.HasFreeEdges)
                    entry.Icon = "Warning.ico";
            }
        }
        else
        {
            entry.Gray = true;
            entry.Icon = "Unactive.ico";
        }
        entry.Invalid = !item.Valid;
        // UpdateNumberOfStepControls
        if (item is Step step)
        {
            int count = step.GetNumberOfStepControls();
            if (count > 0) entry.Text = step.Name + " (Step Controls: " + count + ")";
        }
    }

    /// <summary>SetSplitSubPartNodeStatus: a split sub part shows the state of its first visible cell.</summary>
    public static void SplitSubPartStatus(ModelTreeEntry entry, Controller controller)
    {
        var visible = entry.Children.FirstOrDefault(c => c.Item != null && c.Item.Visible);
        if (visible == null)
        {
            entry.Gray = true;
            entry.Icon = "Hide.ico";
            return;
        }
        entry.Icon = visible.Icon;
        if (entry.Children.Any(c => c.Item is GeometryPart cell && controller.HasSmallFeatures(cell.Name)))
            entry.Icon = SmallFeatures(entry.Icon);
    }

    static string SmallFeatures(string image) => image switch
    {
        "Solid.ico" or "Solid_transparent.ico" or "Shell.ico" or "Shell_transparent.ico" or "Compound.ico" or
        "Compound_transparent.ico" => image.Replace(".ico", "_small_features.ico"),
        _ => image,
    };

    /// <summary>CanRename for an item node (group and split sub part nodes are renameable as well).</summary>
    public static bool CanRename(NamedClass item) =>
        item is BasePart || item is MeshSetupItem || item is FeNodeSet || item is FeElementSet || item is FeSurface ||
        item is FeReferencePoint || item is CoordinateSystem || item is Material || item is Section || item is Constraint ||
        item is SurfaceInteraction || item is ContactPair || item is Distribution || item is Amplitude ||
        item is InitialCondition || item is Step || item is HistoryOutput || item is FieldOutput ||
        item is BoundaryCondition || item is Load || item is DefinedField || item is AnalysisJob ||
        item is ResultFieldOutput || item is ResultHistoryOutput;

    /// <summary>TryGetCompoundSubParts. compoundNames[i] is the compound the i-th action node hangs under
    /// (directly or through a split sub part node), null when it is not a compound sub part node;
    /// singleSplitCompound is set when the only action node is a compound shown as the part it was cut from.</summary>
    static bool CompoundSubParts(Controller controller, string singleSplitCompound, string[] compoundNames, string[] cellNames,
                                 out CompoundGeometryPart compound, out string[] cells)
    {
        compound = null;
        cells = null;
        if (singleSplitCompound != null)
        {
            compound = (CompoundGeometryPart)controller.GetGeometryPart(singleSplitCompound);
            cells = compound.SubPartNames.ToArray();
            return true;
        }
        if (cellNames.Length == 0) return false;
        var names = new List<string>();
        for (int i = 0; i < cellNames.Length; i++)
        {
            if (compoundNames[i] == null || controller.GetGeometryPart(cellNames[i]) == null) return false;
            if (controller.GetGeometryPart(compoundNames[i]) is not CompoundGeometryPart nodeCompound) return false;
            if (compound == null) compound = nodeCompound;
            else if (compound != nodeCompound) return false;
            names.Add(cellNames[i]);
        }
        cells = names.ToArray();
        return true;
    }

    /// <summary>TryGetBodiesToFuse: two or more sub parts of one compound. Returns [compound, cells...] or null.</summary>
    public static string[] BodiesToFuse(Controller controller, string singleSplitCompound, string[] compoundNames, string[] cellNames)
    {
        if (!CompoundSubParts(controller, singleSplitCompound, compoundNames, cellNames, out var compound, out var cells) || cells.Length < 2)
            return null;
        return new[] { compound.Name }.Concat(cells).ToArray();
    }

    /// <summary>TryGetSplitCellsToGroup: cells of one compound that are not already the whole of one sub part.
    /// Returns [compound, cells...] or null.</summary>
    public static string[] SplitCellsToGroup(Controller controller, string[] compoundNames, string[] cellNames)
    {
        if (cellNames.Length == 0 || !CompoundSubParts(controller, null, compoundNames, cellNames, out var compound, out var names))
            return null;
        if (!compound.HasCellSubParts)
        {
            if (names.Distinct().Count() < 2) return null;
        }
        else
        {
            var subParts = new HashSet<string>();
            foreach (string name in names)
                subParts.Add(compound.CellSubPartNames[Array.IndexOf(compound.SubPartNames, name)]);
            if (subParts.Count == 1 && compound.GetCellNames(subParts.First()).Length == names.Length) return null;
        }
        return new[] { compound.Name }.Concat(names).ToArray();
    }

    /// <summary>Annotates an item entry (status, menu fields).</summary>
    public static ModelTreeEntry Annotate(ModelTreeEntry entry, NamedClass item, string view, Controller controller, bool subPart = false)
    {
        entry.Item = item;
        Status(entry, item, controller);
        entry.Menu = ItemFields(item, view, subPart);
        return entry;
    }
}
