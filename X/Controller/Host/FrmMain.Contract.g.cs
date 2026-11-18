// Generated presentation contract from original FrmMain signatures.
using CaeGlobals; using CaeJob; using CaeMesh; using CaeModel; using CaeResults; using FileInOut.Output; using PrePoMax.Commands; using PrePoMax.Forms; using PrePoMax.Python; using System; using System.Collections.Generic; using System.Drawing; using System.Threading.Tasks; using System.Windows.Forms; using UserControls; using vtkControl;
namespace PrePoMax { public partial class FrmMain {
public Controller Controller {get; set;}
public void SetCurrentView(ViewGeometryModelResults view)
{
    var args = new object[]
    {
        view
    };
    InvokePresentation("SetCurrentView", args);
}
public void SetCurrentEdgesVisibilities(vtkControl.vtkEdgesVisibility edgesVisibility)
{
    var args = new object[]
    {
        edgesVisibility
    };
    InvokePresentation("SetCurrentEdgesVisibilities", args);
}
public bool ScreenUpdating {get; set;}
public bool RenderingOn {get; set;}
public bool LastOpenResultsAccepted {get; set;}
public void SetMenuAndToolStripVisibility()
{
    var args = new object[]
    {
    };
    InvokePresentation("SetMenuAndToolStripVisibility", args);
}
public void Open(string fileName, Action<string, string> ActionOnFile, bool resetCamera = true, string parameters = null)
{
    var args = new object[]
    {
        fileName,
        ActionOnFile,
        resetCamera,
        parameters
    };
    InvokePresentation("Open", args);
}
public void UpdateRecentFilesThreadSafe()
{
    var args = new object[]
    {
    };
    InvokePresentation("UpdateRecentFilesThreadSafe", args);
}
public void EnableDisableUndoRedo(string undo, string redo)
{
    var args = new object[]
    {
        undo,
        redo
    };
    InvokePresentation("EnableDisableUndoRedo", args);
}
public SidePanelsState GetSidePanelsState()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<SidePanelsState>("GetSidePanelsState", args);
    return result;
}
public void SetPendingSidePanelsState(SidePanelsState state)
{
    var args = new object[]
    {
        state
    };
    InvokePresentation("SetPendingSidePanelsState", args);
}
public void SetRotationPoint(double[] rotationPoint)
{
    var args = new object[]
    {
        rotationPoint
    };
    InvokePresentation("SetRotationPoint", args);
}
public void UpdateUserViewsThreadSafe(string[] viewNames)
{
    var args = new object[]
    {
        viewNames
    };
    InvokePresentation("UpdateUserViewsThreadSafe", args);
}
public void SetAnnotateWithColor(AnnotateWithColorEnum annotateWithColor)
{
    var args = new object[]
    {
        annotateWithColor
    };
    InvokePresentation("SetAnnotateWithColor", args);
}
public MeshSetupItem EditMeshingParametersFromHistory(MeshSetupItem meshSetupItem)
{
    var args = new object[]
    {
        meshSetupItem
    };
    var result = QueryPresentation<MeshSetupItem>("EditMeshingParametersFromHistory", args);
    return result;
}
public void ShowSplitMeshResults()
{
    var args = new object[]
    {
    };
    InvokePresentation("ShowSplitMeshResults", args);
}
public void SaveAutomationScreenshot(string fileName, bool transparentBackground, int magnification)
{
    var args = new object[]
    {
        fileName,
        transparentBackground,
        magnification
    };
    InvokePresentation("SaveAutomationScreenshot", args);
}
public bool IsWindowHidden {get; set;}
public void SelectResultsUnitSystem(string parameters = null)
{
    var args = new object[]
    {
        parameters
    };
    InvokePresentation("SelectResultsUnitSystem", args);
}
public void UpdateUnitSystem(UnitSystem unitSystem)
{
    var args = new object[]
    {
        unitSystem
    };
    InvokePresentation("UpdateUnitSystem", args);
}
public void RunHistoryPostprocessing()
{
    var args = new object[]
    {
    };
    InvokePresentation("RunHistoryPostprocessing", args);
}
public void RunHistoryPostprocessing(bool? answerToAsk)
{
    var args = new object[]
    {
        answerToAsk
    };
    InvokePresentation("RunHistoryPostprocessing", args);
}
public void OpenAnalysisResults(string jobName, bool asynchronous = true)
{
    var args = new object[]
    {
        jobName,
        asynchronous
    };
    InvokePresentation("OpenAnalysisResults", args);
}
public void UpdateAnalysisProgress(string jobName, JobStatus jobStatus)
{
    var args = new object[]
    {
        jobName,
        jobStatus
    };
    InvokePresentation("UpdateAnalysisProgress", args);
}
public AnalysisJob GetDefaultJob()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<AnalysisJob>("GetDefaultJob", args);
    return result;
}
public string GetDefaultJobName()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<string>("GetDefaultJobName", args);
    return result;
}
public void SelectionChanged(int[] ids = null)
{
    var args = new object[]
    {
        ids
    };
    InvokePresentation("SelectionChanged", args);
}
public void SetQuerySelection(bool querySelection)
{
    var args = new object[]
    {
        querySelection
    };
    InvokePresentation("SetQuerySelection", args);
}
public bool GetQuerySelection()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<bool>("GetQuerySelection", args);
    return result;
}
public void SetSelectBy(vtkSelectBy selectBy)
{
    var args = new object[]
    {
        selectBy
    };
    InvokePresentation("SetSelectBy", args);
}
public void SetSelectItem(vtkSelectItem selectItem)
{
    var args = new object[]
    {
        selectItem
    };
    InvokePresentation("SetSelectItem", args);
}
public void GetGeometryPickProperties(double[] point, out int elementId, out int[] edgeNodeIds, out int[] cellFaceNodeIds, string[] selectionPartNames = null)
{
    var args = new object[]
    {
        point,
        null,
        null,
        null,
        selectionPartNames
    };
    QueryPresentation<object>("GetGeometryPickProperties", args);
    elementId = (int)args[1];
    edgeNodeIds = (int[])args[2];
    cellFaceNodeIds = (int[])args[3];
}
public void GetClosestCellsOnParts(double[] point, string[] partNames, out double[] distances, out double[][] normals)
{
    var args = new object[]
    {
        point,
        partNames,
        null,
        null
    };
    QueryPresentation<object>("GetClosestCellsOnParts", args);
    distances = (double[])args[2];
    normals = (double[][])args[3];
}
public double GetSelectionPrecision()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<double>("GetSelectionPrecision", args);
    return result;
}
public void GetPointAndCellIdsInsideFrustum(double[][] planeParameters, string[] selectionPartNames, out int[] pointIds, out int[] cellIds)
{
    var args = new object[]
    {
        planeParameters,
        selectionPartNames,
        null,
        null
    };
    QueryPresentation<object>("GetPointAndCellIdsInsideFrustum", args);
    pointIds = (int[])args[2];
    cellIds = (int[])args[3];
}
public void CloseAllForms()
{
    var args = new object[]
    {
    };
    InvokePresentation("CloseAllForms", args);
}
public void SelectOneNameInSymbolsNames(string name)
{
    var args = new object[]
    {
        name
    };
    InvokePresentation("SelectOneNameInSymbolsNames", args);
}
public void SetResultNames()
{
    var args = new object[]
    {
    };
    InvokePresentation("SetResultNames", args);
}
public void SetCurrentResults(string resultsName)
{
    var args = new object[]
    {
        resultsName
    };
    InvokePresentation("SetCurrentResults", args);
}
public string GetDeformationVariable()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<string>("GetDeformationVariable", args);
    return result;
}
public DeformationScaleFactorTypeEnum GetDeformationType()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<DeformationScaleFactorTypeEnum>("GetDeformationType", args);
    return result;
}
public float GetDeformationFactor()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<float>("GetDeformationFactor", args);
    return result;
}
public void SetDeformationType(DeformationScaleFactorTypeEnum deformationType)
{
    var args = new object[]
    {
        deformationType
    };
    InvokePresentation("SetDeformationType", args);
}
public void SetDeformationFactor(float deformationFactor)
{
    var args = new object[]
    {
        deformationFactor
    };
    InvokePresentation("SetDeformationFactor", args);
}
public ComplexResultTypeEnum GetComplexResultType()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<ComplexResultTypeEnum>("GetComplexResultType", args);
    return result;
}
public double GetComplexAngleDeg()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<double>("GetComplexAngleDeg", args);
    return result;
}
public void SetStateReady(string currentText)
{
    var args = new object[]
    {
        currentText
    };
    InvokePresentation("SetStateReady", args);
}
public bool SetStateWorking(string text, bool showCancelButton = false)
{
    var args = new object[]
    {
        text,
        showCancelButton
    };
    var result = QueryPresentation<bool>("SetStateWorking", args);
    return result;
}
public bool IsStateOpening()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<bool>("IsStateOpening", args);
    return result;
}
public void SetTitle(string title)
{
    var args = new object[]
    {
        title
    };
    InvokePresentation("SetTitle", args);
}
public string GetFileNameToOpen(string title)
{
    var args = new object[]
    {
        title
    };
    var result = QueryPresentation<string>("GetFileNameToOpen", args);
    return result;
}
public string GetFileNameToOpen(string title, string filter)
{
    var args = new object[]
    {
        title,
        filter
    };
    var result = QueryPresentation<string>("GetFileNameToOpen", args);
    return result;
}
public string GetFileNameToImport(string title, bool onlyMaterials)
{
    var args = new object[]
    {
        title,
        onlyMaterials
    };
    var result = QueryPresentation<string>("GetFileNameToImport", args);
    return result;
}
public string GetFileNameToImport(string title, string filter)
{
    var args = new object[]
    {
        title,
        filter
    };
    var result = QueryPresentation<string>("GetFileNameToImport", args);
    return result;
}
public string GetFileNameToSaveAs()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<string>("GetFileNameToSaveAs", args);
    return result;
}
public void ClearControls()
{
    var args = new object[]
    {
    };
    InvokePresentation("ClearControls", args);
}
public void ClearResults()
{
    var args = new object[]
    {
    };
    InvokePresentation("ClearResults", args);
}
public void Clear3D()
{
    var args = new object[]
    {
    };
    InvokePresentation("Clear3D", args);
}
public void ClearButKeepParts()
{
    var args = new object[]
    {
    };
    InvokePresentation("ClearButKeepParts", args);
}
public void Clear3DSelection()
{
    var args = new object[]
    {
    };
    InvokePresentation("Clear3DSelection", args);
}
public void ClearActiveTreeSelection()
{
    var args = new object[]
    {
    };
    InvokePresentation("ClearActiveTreeSelection", args);
}
public void GetViewParameters(out double[] position, out double[] focalPoint, out double[] viewUp, out double parallelScale)
{
    var args = new object[]
    {
        null,
        null,
        null,
        null
    };
    QueryPresentation<object>("GetViewParameters", args);
    position = (double[])args[0];
    focalPoint = (double[])args[1];
    viewUp = (double[])args[2];
    parallelScale = (double)args[3];
}
public void SetViewParameters(bool animate, double[] position, double[] focalPoint, double[] viewUp, double parallelScale)
{
    var args = new object[]
    {
        animate,
        position,
        focalPoint,
        viewUp,
        parallelScale
    };
    InvokePresentation("SetViewParameters", args);
}
public void SetFrontBackView(bool animate, bool front)
{
    var args = new object[]
    {
        animate,
        front
    };
    InvokePresentation("SetFrontBackView", args);
}
public void SetStandardView(string orientation, bool animate)
{
    var args = new object[]
    {
        orientation,
        animate
    };
    InvokePresentation("SetStandardView", args);
}
public void SetZoomToFit(bool animate)
{
    var args = new object[]
    {
        animate
    };
    InvokePresentation("SetZoomToFit", args);
}
public void Rotate(double azimuthAngle, double elevationAngle, double rollAngle)
{
    var args = new object[]
    {
        azimuthAngle,
        elevationAngle,
        rollAngle
    };
    InvokePresentation("Rotate", args);
}
public double[] GetViewPlaneNormal()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<double[]>("GetViewPlaneNormal", args);
    return result;
}
public void AdjustCameraDistanceAndClipping()
{
    var args = new object[]
    {
    };
    InvokePresentation("AdjustCameraDistanceAndClipping", args);
}
public void SuspendCameraAdjustment()
{
    var args = new object[]
    {
    };
    InvokePresentation("SuspendCameraAdjustment", args);
}
public void ResumeCameraAdjustment()
{
    var args = new object[]
    {
    };
    InvokePresentation("ResumeCameraAdjustment", args);
}
public void UpdateScalarsAndRedraw()
{
    var args = new object[]
    {
    };
    InvokePresentation("UpdateScalarsAndRedraw", args);
}
public void UpdateScalarsAndCameraAndRedraw()
{
    var args = new object[]
    {
    };
    InvokePresentation("UpdateScalarsAndCameraAndRedraw", args);
}
public vtkMaxActorData[] GetVtkMaxActorData()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<vtkMaxActorData[]>("GetVtkMaxActorData", args);
    return result;
}
public vtkMaxLookupTable GetLookupTable()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<vtkMaxLookupTable>("GetLookupTable", args);
    return result;
}
public double[] GetClosestUpView()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<double[]>("GetClosestUpView", args);
    return result;
}
public void CreateSectionView(double[] point, double[] normal, bool lightenColors, Color sectionColor, bool elementWise, bool hatch)
{
    var args = new object[]
    {
        point,
        normal,
        lightenColors,
        sectionColor,
        elementWise,
        hatch
    };
    InvokePresentation("CreateSectionView", args);
}
public void UpdateSectionView(double[] point, double[] normal, bool lightenColors, Color sectionColor, bool elementWise, bool hatch)
{
    var args = new object[]
    {
        point,
        normal,
        lightenColors,
        sectionColor,
        elementWise,
        hatch
    };
    InvokePresentation("UpdateSectionView", args);
}
public void RemoveSectionView(bool releaseVolumeGrids = false)
{
    var args = new object[]
    {
        releaseVolumeGrids
    };
    InvokePresentation("RemoveSectionView", args);
}
public void PreviewExplodedView(Dictionary<string, double[]> partOffsets, bool animate, int timeMs)
{
    var args = new object[]
    {
        partOffsets,
        animate,
        timeMs
    };
    InvokePresentation("PreviewExplodedView", args);
}
public void RemovePreviewedExplodedView(string[] partNames)
{
    var args = new object[]
    {
        partNames
    };
    InvokePresentation("RemovePreviewedExplodedView", args);
}
public void SetExplodedViewStatus(bool status)
{
    var args = new object[]
    {
        status
    };
    InvokePresentation("SetExplodedViewStatus", args);
}
public void ApplyFollowerView(string[] partName, int[] nodeIds)
{
    var args = new object[]
    {
        partName,
        nodeIds
    };
    InvokePresentation("ApplyFollowerView", args);
}
public void UpdateFollowerView()
{
    var args = new object[]
    {
    };
    InvokePresentation("UpdateFollowerView", args);
}
public void RemoveFollowerView()
{
    var args = new object[]
    {
    };
    InvokePresentation("RemoveFollowerView", args);
}
public void AddSymmetry(int symmetryPlane, double[] symmetryPoint)
{
    var args = new object[]
    {
        symmetryPlane,
        symmetryPoint
    };
    InvokePresentation("AddSymmetry", args);
}
public void AddLinearPattern(double[] displacement, int numOfItems)
{
    var args = new object[]
    {
        displacement,
        numOfItems
    };
    InvokePresentation("AddLinearPattern", args);
}
public void AddCircularPattern(double[] axisPoint, double[] axisNormal, double angle, int numOfItems)
{
    var args = new object[]
    {
        axisPoint,
        axisNormal,
        angle,
        numOfItems
    };
    InvokePresentation("AddCircularPattern", args);
}
public void ApplyTransformations()
{
    var args = new object[]
    {
    };
    InvokePresentation("ApplyTransformations", args);
}
public void SetTransformationsStatus(bool status)
{
    var args = new object[]
    {
        status
    };
    InvokePresentation("SetTransformationsStatus", args);
}
public void HideTransformedActors()
{
    var args = new object[]
    {
    };
    InvokePresentation("HideTransformedActors", args);
}
public vtkMaxActor Add3DNodes(vtkMaxActorData nodeData)
{
    var args = new object[]
    {
        nodeData
    };
    var result = QueryPresentation<vtkMaxActor>("Add3DNodes", args);
    return result;
}
public vtkMaxActor Add3DCells(vtkMaxActorData cellData)
{
    var args = new object[]
    {
        cellData
    };
    var result = QueryPresentation<vtkMaxActor>("Add3DCells", args);
    return result;
}
public void Add3DCells(vtkMaxActorData[] cellData)
{
    var args = new object[]
    {
        cellData
    };
    InvokePresentation("Add3DCells", args);
}
public void AddActor(vtkMaxActor actor)
{
    var args = new object[]
    {
        actor
    };
    InvokePresentation("AddActor", args);
}
public void AddScalarFieldOn3DCells(vtkMaxActorData actorData, bool update)
{
    var args = new object[]
    {
        actorData,
        update
    };
    InvokePresentation("AddScalarFieldOn3DCells", args);
}
public void AddVectorFieldActor(vtkMaxActorData actorData, double maxMagnitude, double maxArrowLength, double arrowSize)
{
    var args = new object[]
    {
        actorData,
        maxMagnitude,
        maxArrowLength,
        arrowSize
    };
    InvokePresentation("AddVectorFieldActor", args);
}
public void AddTensorFieldActor(vtkMaxActorData actorData, double maxAbsValue, double maxGlyphLength, double arrowSize)
{
    var args = new object[]
    {
        actorData,
        maxAbsValue,
        maxGlyphLength,
        arrowSize
    };
    InvokePresentation("AddTensorFieldActor", args);
}
public bool AddAnimatedVectorFieldActor(vtkMaxActorData actorData, double maxMagnitude, double maxArrowLength, double arrowSize)
{
    var args = new object[]
    {
        actorData,
        maxMagnitude,
        maxArrowLength,
        arrowSize
    };
    var result = QueryPresentation<bool>("AddAnimatedVectorFieldActor", args);
    return result;
}
public bool AddAnimatedTensorFieldActor(vtkMaxActorData actorData, double maxAbsValue, double maxGlyphLength, double arrowSize)
{
    var args = new object[]
    {
        actorData,
        maxAbsValue,
        maxGlyphLength,
        arrowSize
    };
    var result = QueryPresentation<bool>("AddAnimatedTensorFieldActor", args);
    return result;
}
public bool AddAnimatedScalarFieldOn3DCells(vtkMaxActorData actorData)
{
    var args = new object[]
    {
        actorData
    };
    var result = QueryPresentation<bool>("AddAnimatedScalarFieldOn3DCells", args);
    return result;
}
public void UpdateActorSurfaceScalarField(string actorName, float[] values, NodesExchangeData extremeNodes, ResultFieldExchangeData resultField, bool update)
{
    var args = new object[]
    {
        actorName,
        values,
        extremeNodes,
        resultField,
        update
    };
    InvokePresentation("UpdateActorSurfaceScalarField", args);
}
public void UpdateActorColorContoursVisibility(string[] actorNames, bool colorContour)
{
    var args = new object[]
    {
        actorNames,
        colorContour
    };
    InvokePresentation("UpdateActorColorContoursVisibility", args);
}
public void UpdateResultRepresentationVisibility(string[] partNames, bool visible, bool update)
{
    var args = new object[]
    {
        partNames,
        visible,
        update
    };
    InvokePresentation("UpdateResultRepresentationVisibility", args);
}
public void AddSphereActor(vtkMaxActorData actorData, double symbolSize)
{
    var args = new object[]
    {
        actorData,
        symbolSize
    };
    InvokePresentation("AddSphereActor", args);
}
public void AddCoordinateSystemSymbol(double[] origin, double[][] axisDirections, string[] labels, double symbolSize, vtkRendererLayer layer)
{
    var args = new object[]
    {
        origin,
        axisDirections,
        labels,
        symbolSize,
        layer
    };
    InvokePresentation("AddCoordinateSystemSymbol", args);
}
public void AddMaterialAxesSymbol(double[] origin, double[][] axisDirections, string[] labels, double symbolSize)
{
    var args = new object[]
    {
        origin,
        axisDirections,
        labels,
        symbolSize
    };
    InvokePresentation("AddMaterialAxesSymbol", args);
}
public void AddCaptionActor(string name, string caption, Color color, double[] position, double[] offsetVector, double fontScaleFactor, vtkRendererLayer layer)
{
    var args = new object[]
    {
        name,
        caption,
        color,
        position,
        offsetVector,
        fontScaleFactor,
        layer
    };
    InvokePresentation("AddCaptionActor", args);
}
public void AddLabelActor(string name, double[][] positions, int[] labels, Color color, double fontScaleFactor, vtkRendererLayer layer)
{
    var args = new object[]
    {
        name,
        positions,
        labels,
        color,
        fontScaleFactor,
        layer
    };
    InvokePresentation("AddLabelActor", args);
}
public void AddLabelActor(string name, double[][] positions, string[] labels, Color color, double fontScaleFactor, vtkRendererLayer layer)
{
    var args = new object[]
    {
        name,
        positions,
        labels,
        color,
        fontScaleFactor,
        layer
    };
    InvokePresentation("AddLabelActor", args);
}
public void RemoveOverlayActors(string[] actorNames)
{
    var args = new object[]
    {
        actorNames
    };
    InvokePresentation("RemoveOverlayActors", args);
}
public void AddMeasurementAnnotation(string name, vtkMaxActorData nodeData, vtkMaxActorData lineData, double[][] arrowCoordinates, double[][] arrowNormals, double symbolSize, bool visible)
{
    var args = new object[]
    {
        name,
        nodeData,
        lineData,
        arrowCoordinates,
        arrowNormals,
        symbolSize,
        visible
    };
    InvokePresentation("AddMeasurementAnnotation", args);
}
public void UpdateMeasurementAnnotation(string name, double[][] nodeCoordinates, double[][] lineCoordinates, double[][] arrowCoordinates, double[][] arrowNormals, bool visible)
{
    var args = new object[]
    {
        name,
        nodeCoordinates,
        lineCoordinates,
        arrowCoordinates,
        arrowNormals,
        visible
    };
    InvokePresentation("UpdateMeasurementAnnotation", args);
}
public void RemoveMeasurementAnnotations(string[] names)
{
    var args = new object[]
    {
        names
    };
    InvokePresentation("RemoveMeasurementAnnotations", args);
}
public void UpdateOverlayPointsActor(string actorName, double[][] coordinates)
{
    var args = new object[]
    {
        actorName,
        coordinates
    };
    InvokePresentation("UpdateOverlayPointsActor", args);
}
public void UpdateOverlayCaptionActorPosition(string actorName, double[] position)
{
    var args = new object[]
    {
        actorName,
        position
    };
    InvokePresentation("UpdateOverlayCaptionActorPosition", args);
}
public void AddOrientedDisplacementConstraintActor(vtkMaxActorData actorData, double symbolSize)
{
    var args = new object[]
    {
        actorData,
        symbolSize
    };
    InvokePresentation("AddOrientedDisplacementConstraintActor", args);
}
public void AddOrientedConeActors(vtkMaxActorData data, double symbolSize)
{
    var args = new object[]
    {
        data,
        symbolSize
    };
    InvokePresentation("AddOrientedConeActors", args);
}
public void AddOrientedRotationalConstraintActor(vtkMaxActorData actorData, double symbolSize)
{
    var args = new object[]
    {
        actorData,
        symbolSize
    };
    InvokePresentation("AddOrientedRotationalConstraintActor", args);
}
public void AddOrientedJointActor(vtkMaxActorData actorData, double symbolSize, vtkJointSymbolEnum symbol)
{
    var args = new object[]
    {
        actorData,
        symbolSize,
        symbol
    };
    InvokePresentation("AddOrientedJointActor", args);
}
public void AddOrientedArrowsActor(vtkMaxActorData actorData, double symbolSize, bool invert = false, double relativeSize = 1)
{
    var args = new object[]
    {
        actorData,
        symbolSize,
        invert,
        relativeSize
    };
    InvokePresentation("AddOrientedArrowsActor", args);
}
public void AddOrientedDoubleArrowsActor(vtkMaxActorData actorData, double symbolSize)
{
    var args = new object[]
    {
        actorData,
        symbolSize
    };
    InvokePresentation("AddOrientedDoubleArrowsActor", args);
}
public void AddOrientedSpringActor(vtkMaxActorData actorData, double symbolSize, bool invert = false)
{
    var args = new object[]
    {
        actorData,
        symbolSize,
        invert
    };
    InvokePresentation("AddOrientedSpringActor", args);
}
public void AddOrientedThermosActor(vtkMaxActorData actorData, double symbolSize, bool invert = false)
{
    var args = new object[]
    {
        actorData,
        symbolSize,
        invert
    };
    InvokePresentation("AddOrientedThermosActor", args);
}
public void AddOrientedFluxActor(vtkMaxActorData actorData, double symbolSize, bool center, bool invert)
{
    var args = new object[]
    {
        actorData,
        symbolSize,
        center,
        invert
    };
    InvokePresentation("AddOrientedFluxActor", args);
}
public bool ContainsActor(string actorName)
{
    var args = new object[]
    {
        actorName
    };
    var result = QueryPresentation<bool>("ContainsActor", args);
    return result;
}
public void HighlightActor(string actorName)
{
    var args = new object[]
    {
        actorName
    };
    InvokePresentation("HighlightActor", args);
}
public void UpdateActor(string oldName, string newName, Color newColor)
{
    var args = new object[]
    {
        oldName,
        newName,
        newColor
    };
    InvokePresentation("UpdateActor", args);
}
public bool UpdateActorsColorTables(string[] actorNames, Color[][] colorTables)
{
    var args = new object[]
    {
        actorNames,
        colorTables
    };
    var result = QueryPresentation<bool>("UpdateActorsColorTables", args);
    return result;
}
public void UpdateActorModelEdgesToDraw(string actorName, PartExchangeData modelEdgesToDraw)
{
    var args = new object[]
    {
        actorName,
        modelEdgesToDraw
    };
    InvokePresentation("UpdateActorModelEdgesToDraw", args);
}
public void HideActors(string[] actorNames, bool updateColorContours)
{
    var args = new object[]
    {
        actorNames,
        updateColorContours
    };
    InvokePresentation("HideActors", args);
}
public void ShowActors(string[] actorNames, bool updateColorContours)
{
    var args = new object[]
    {
        actorNames,
        updateColorContours
    };
    InvokePresentation("ShowActors", args);
}
public void SetCoorSysVisibility(bool visibility)
{
    var args = new object[]
    {
        visibility
    };
    InvokePresentation("SetCoorSysVisibility", args);
}
public void SetScaleWidgetVisibility(bool visibility)
{
    var args = new object[]
    {
        visibility
    };
    InvokePresentation("SetScaleWidgetVisibility", args);
}
public void SetWidgetHighlightEnabled(bool enabled)
{
    var args = new object[]
    {
        enabled
    };
    InvokePresentation("SetWidgetHighlightEnabled", args);
}
public void SetSelectionDistance(int distanceInPixels)
{
    var args = new object[]
    {
        distanceInPixels
    };
    InvokePresentation("SetSelectionDistance", args);
}
public void InitializeResultWidgetPositions()
{
    var args = new object[]
    {
    };
    InvokePresentation("InitializeResultWidgetPositions", args);
}
public void SetScalarBarColorSpectrum(vtkControl.vtkMaxColorSpectrum colorSpectrum)
{
    var args = new object[]
    {
        colorSpectrum
    };
    InvokePresentation("SetScalarBarColorSpectrum", args);
}
public void SetScalarBarVisibility(bool visibility)
{
    var args = new object[]
    {
        visibility
    };
    InvokePresentation("SetScalarBarVisibility", args);
}
public void SetScalarBarNumberFormat(string numberFormat)
{
    var args = new object[]
    {
        numberFormat
    };
    InvokePresentation("SetScalarBarNumberFormat", args);
}
public void SetScalarBarText(string fieldName, string componentName, string unitAbbreviation, string complexComponent, string minMaxType)
{
    var args = new object[]
    {
        fieldName,
        componentName,
        unitAbbreviation,
        complexComponent,
        minMaxType
    };
    InvokePresentation("SetScalarBarText", args);
}
public void DrawLegendBackground(bool drawBackground)
{
    var args = new object[]
    {
        drawBackground
    };
    InvokePresentation("DrawLegendBackground", args);
}
public void DrawLegendBorder(bool drawBorder)
{
    var args = new object[]
    {
        drawBorder
    };
    InvokePresentation("DrawLegendBorder", args);
}
public void InitializeColorBarWidgetPosition()
{
    var args = new object[]
    {
    };
    InvokePresentation("InitializeColorBarWidgetPosition", args);
}
public void SetColorBarColorsAndLabels(Color[] colors, string[] labels)
{
    var args = new object[]
    {
        colors,
        labels
    };
    InvokePresentation("SetColorBarColorsAndLabels", args);
}
public void AddColorBarColorsAndLabels(Color[] colors, string[] labels)
{
    var args = new object[]
    {
        colors,
        labels
    };
    InvokePresentation("AddColorBarColorsAndLabels", args);
}
public void DrawColorBarBackground(bool drawBackground)
{
    var args = new object[]
    {
        drawBackground
    };
    InvokePresentation("DrawColorBarBackground", args);
}
public void DrawColorBarBorder(bool drawBorder)
{
    var args = new object[]
    {
        drawBorder
    };
    InvokePresentation("DrawColorBarBorder", args);
}
public void HideColorBar()
{
    var args = new object[]
    {
    };
    InvokePresentation("HideColorBar", args);
}
public void SetStatusBlockVisibility(bool draw)
{
    var args = new object[]
    {
        draw
    };
    InvokePresentation("SetStatusBlockVisibility", args);
}
public void SetStatusBlockNumberFormat(string numberFormat)
{
    var args = new object[]
    {
        numberFormat
    };
    InvokePresentation("SetStatusBlockNumberFormat", args);
}
public void DrawStatusBlockBackground(bool drawBackground)
{
    var args = new object[]
    {
        drawBackground
    };
    InvokePresentation("DrawStatusBlockBackground", args);
}
public void DrawStatusBlockBorder(bool drawBorder)
{
    var args = new object[]
    {
        drawBorder
    };
    InvokePresentation("DrawStatusBlockBorder", args);
}
public void SetStatusBlock(string name, DateTime dateTime, float analysisTime, string unit, string deformationVariable, float scaleFactor, vtkControl.vtkMaxFieldDataType fieldType, int stepNumber, int incrementNumber, int nodalDiameter)
{
    var args = new object[]
    {
        name,
        dateTime,
        analysisTime,
        unit,
        deformationVariable,
        scaleFactor,
        fieldType,
        stepNumber,
        incrementNumber,
        nodalDiameter
    };
    InvokePresentation("SetStatusBlock", args);
}
public void SetBackground(bool gradient, Color topColor, Color bottomColor, bool redraw)
{
    var args = new object[]
    {
        gradient,
        topColor,
        bottomColor,
        redraw
    };
    InvokePresentation("SetBackground", args);
}
public void SetLighting(double ambient, double diffuse, bool redraw)
{
    var args = new object[]
    {
        ambient,
        diffuse,
        redraw
    };
    InvokePresentation("SetLighting", args);
}
public void SetAmbientOcclusion(bool enabled, double relativeRadius, int kernelSize, bool redraw)
{
    var args = new object[]
    {
        enabled,
        relativeRadius,
        kernelSize,
        redraw
    };
    InvokePresentation("SetAmbientOcclusion", args);
}
public void SetNavigationSensitivity(double rotateSensitivity, double zoomSensitivity, bool invertZoom, bool smoothZoom)
{
    var args = new object[]
    {
        rotateSensitivity,
        zoomSensitivity,
        invertZoom,
        smoothZoom
    };
    InvokePresentation("SetNavigationSensitivity", args);
}
public void SetTrackpadNavigation(bool enabled, bool useWheelFallback, bool twoFingerDragPans, double panSensitivity, bool invertX, bool invertY)
{
    var args = new object[]
    {
        enabled,
        useWheelFallback,
        twoFingerDragPans,
        panSensitivity,
        invertX,
        invertY
    };
    InvokePresentation("SetTrackpadNavigation", args);
}
public void SetSmoothing(bool pointSmoothing, bool lineSmoothing, bool redraw)
{
    var args = new object[]
    {
        pointSmoothing,
        lineSmoothing,
        redraw
    };
    InvokePresentation("SetSmoothing", args);
}
public void SetHighlightColor(Color primaryHighlightColor, Color secondaryHighlightColor)
{
    var args = new object[]
    {
        primaryHighlightColor,
        secondaryHighlightColor
    };
    InvokePresentation("SetHighlightColor", args);
}
public void SetMouseHighlightColor(Color mouseHighlightColor)
{
    var args = new object[]
    {
        mouseHighlightColor
    };
    InvokePresentation("SetMouseHighlightColor", args);
}
public void SetDrawSymbolEdges(bool drawSilhouettes)
{
    var args = new object[]
    {
        drawSilhouettes
    };
    InvokePresentation("SetDrawSymbolEdges", args);
}
public void CropPartWithCylinder(string partName, double r, string fileName)
{
    var args = new object[]
    {
        partName,
        r,
        fileName
    };
    InvokePresentation("CropPartWithCylinder", args);
}
public void CropPartWithCube(string partName, double x, double y, double z, double a, string fileName)
{
    var args = new object[]
    {
        partName,
        x,
        y,
        z,
        a,
        fileName
    };
    InvokePresentation("CropPartWithCube", args);
}
public void SmoothPart(string partName, double a, string fileName)
{
    var args = new object[]
    {
        partName,
        a,
        fileName
    };
    InvokePresentation("SmoothPart", args);
}
public void ActivateUserPick()
{
    var args = new object[]
    {
    };
    InvokePresentation("ActivateUserPick", args);
}
public void DeactivateUserPick()
{
    var args = new object[]
    {
    };
    InvokePresentation("DeactivateUserPick", args);
}
public void SetFieldData(string name, string component)
{
    var args = new object[]
    {
        name,
        component
    };
    InvokePresentation("SetFieldData", args);
}
public void SetViewResultsType(ViewResultsTypeEnum viewResultsType)
{
    var args = new object[]
    {
        viewResultsType
    };
    InvokePresentation("SetViewResultsType", args);
}
public void SetResultsUndeformedModelType(UndeformedModelTypeEnum undeformedModelType)
{
    var args = new object[]
    {
        undeformedModelType
    };
    InvokePresentation("SetResultsUndeformedModelType", args);
}
public void SetFieldData(string name, string component, int stepId, int stepIncrementId)
{
    var args = new object[]
    {
        name,
        component,
        stepId,
        stepIncrementId
    };
    InvokePresentation("SetFieldData", args);
}
public void SelectStepAndIncrement(int stepId, int incrementId)
{
    var args = new object[]
    {
        stepId,
        incrementId
    };
    InvokePresentation("SelectStepAndIncrement", args);
}
public void SetAnimationAcceleration(bool animationAcceleration)
{
    var args = new object[]
    {
        animationAcceleration
    };
    InvokePresentation("SetAnimationAcceleration", args);
}
public void SetAnimationFrameData(float[] time, int[] stepId, int[] stepIncrementId, int[] modeNumber, int[] nodalDiameter, float[] scale, double[] allFramesScalarRange, vtkMaxAnimationType animationType)
{
    var args = new object[]
    {
        time,
        stepId,
        stepIncrementId,
        modeNumber,
        nodalDiameter,
        scale,
        allFramesScalarRange,
        animationType
    };
    InvokePresentation("SetAnimationFrameData", args);
}
public void SetAnimationFrame(int frameNum, bool scalarRangeFromAllFrames)
{
    var args = new object[]
    {
        frameNum,
        scalarRangeFromAllFrames
    };
    InvokePresentation("SetAnimationFrame", args);
}
public void SaveAnimationAsAVI(string fileName, int[] firstLastFrame, int step, int fps, bool scalarRangeFromAllFrames, bool swing, bool encoderOptions)
{
    var args = new object[]
    {
        fileName,
        firstLastFrame,
        step,
        fps,
        scalarRangeFromAllFrames,
        swing,
        encoderOptions
    };
    InvokePresentation("SaveAnimationAsAVI", args);
}
public void SaveAnimationAsImages(string fileName, int[] firstLastFrame, int step, bool scalarRangeFromAllFrames, bool swing)
{
    var args = new object[]
    {
        fileName,
        firstLastFrame,
        step,
        scalarRangeFromAllFrames,
        swing
    };
    InvokePresentation("SaveAnimationAsImages", args);
}
public void AddArrowWidget(string name, string text, string numberFormat, double[] anchorPoint, bool drawBackground, bool drawBorder, bool visible)
{
    var args = new object[]
    {
        name,
        text,
        numberFormat,
        anchorPoint,
        drawBackground,
        drawBorder,
        visible
    };
    InvokePresentation("AddArrowWidget", args);
}
public void AddArrowWidget(string name, string text, string numberFormat, double[] anchorPoint, bool drawBackground, bool drawBorder, bool visible, string[] animationActorNames)
{
    var args = new object[]
    {
        name,
        text,
        numberFormat,
        anchorPoint,
        drawBackground,
        drawBorder,
        visible,
        animationActorNames
    };
    InvokePresentation("AddArrowWidget", args);
}
public void UpdateArrowWidgetAnimationData(string name, string text, double[] anchorPoint)
{
    var args = new object[]
    {
        name,
        text,
        anchorPoint
    };
    InvokePresentation("UpdateArrowWidgetAnimationData", args);
}
public bool TryGetAnimationNodeData(int nodeId, out double[] coordinates, out float value)
{
    var args = new object[]
    {
        nodeId,
        null,
        null
    };
    var result = QueryPresentation<bool>("TryGetAnimationNodeData", args);
    coordinates = (double[])args[1];
    value = (float)args[2];
    return result;
}
public void ArrangeVisibleArrowWidgets()
{
    var args = new object[]
    {
    };
    InvokePresentation("ArrangeVisibleArrowWidgets", args);
}
public void RemoveArrowWidgets(string[] widgetNames)
{
    var args = new object[]
    {
        widgetNames
    };
    InvokePresentation("RemoveArrowWidgets", args);
}
public void RegenerateTree(bool remeshing = false)
{
    var args = new object[]
    {
        remeshing
    };
    InvokePresentation("RegenerateTree", args);
}
public void BeginTreeUpdateBatch()
{
    var args = new object[]
    {
    };
    InvokePresentation("BeginTreeUpdateBatch", args);
}
public void EndTreeUpdateBatch()
{
    var args = new object[]
    {
    };
    InvokePresentation("EndTreeUpdateBatch", args);
}
public void AddTreeNode(ViewGeometryModelResults view, NamedClass item, string parentName)
{
    var args = new object[]
    {
        view,
        item,
        parentName
    };
    InvokePresentation("AddTreeNode", args);
}
public void UpdateTreeNode(ViewGeometryModelResults view, string oldItemName, NamedClass item, string parentName, bool updateSelection = true)
{
    var args = new object[]
    {
        view,
        oldItemName,
        item,
        parentName,
        updateSelection
    };
    InvokePresentation("UpdateTreeNode", args);
}
public void UpdateTreeNodeLayout(ViewGeometryModelResults view, string itemName, NamedClass item, string parentName)
{
    var args = new object[]
    {
        view,
        itemName,
        item,
        parentName
    };
    InvokePresentation("UpdateTreeNodeLayout", args);
}
public void SwapTreeNode(ViewGeometryModelResults view, string firstItemName, NamedClass firstItem, string secondItemName, NamedClass secondItem, string parentName)
{
    var args = new object[]
    {
        view,
        firstItemName,
        firstItem,
        secondItemName,
        secondItem,
        parentName
    };
    InvokePresentation("SwapTreeNode", args);
}
public void RemoveTreeNode<T>(ViewGeometryModelResults view, string nodeName, string parentName)
    where T : NamedClass
{
    var args = new object[]
    {
        view,
        nodeName,
        parentName
    };
    InvokePresentation("RemoveTreeNode", args);
}
public bool[][] GetTreeExpandCollapseState()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<bool[][]>("GetTreeExpandCollapseState", args);
    return result;
}
public void SetTreeExpandCollapseState(bool[][] states)
{
    var args = new object[]
    {
        states
    };
    InvokePresentation("SetTreeExpandCollapseState", args);
}
public Dictionary<string, bool>[] GetStableTreeExpandCollapseState()
{
    var args = new object[]
    {
    };
    var result = QueryPresentation<Dictionary<string, bool>[]>("GetStableTreeExpandCollapseState", args);
    return result;
}
public void SetStableTreeExpandCollapseState(Dictionary<string, bool>[] states)
{
    var args = new object[]
    {
        states
    };
    InvokePresentation("SetStableTreeExpandCollapseState", args);
}
public void UpdateHighlight()
{
    var args = new object[]
    {
    };
    InvokePresentation("UpdateHighlight", args);
}
public void SelectBaseParts(string[] partNames)
{
    var args = new object[]
    {
        partNames
    };
    InvokePresentation("SelectBaseParts", args);
}
public void SelectBaseParts(MouseEventArgs e, Keys modifierKeys, string[] partNames)
{
    var args = new object[]
    {
        e,
        modifierKeys,
        partNames
    };
    InvokePresentation("SelectBaseParts", args);
}
public void SelectFirstComponentOfFirstFieldOutput()
{
    var args = new object[]
    {
    };
    InvokePresentation("SelectFirstComponentOfFirstFieldOutput", args);
}
public void SelectFieldOutputComponent(string fieldName, string componentName)
{
    var args = new object[]
    {
        fieldName,
        componentName
    };
    InvokePresentation("SelectFieldOutputComponent", args);
}
public void SetNumberOfModelUserKeywords(int numOfUserKeywords)
{
    var args = new object[]
    {
        numOfUserKeywords
    };
    InvokePresentation("SetNumberOfModelUserKeywords", args);
}
public void SetNumberOfModelModifiedKeywords(int numOfModifiedKeywords)
{
    var args = new object[]
    {
        numOfModifiedKeywords
    };
    InvokePresentation("SetNumberOfModelModifiedKeywords", args);
}
public void WriteDataToOutput(string data)
{
    var args = new object[]
    {
        data
    };
    InvokePresentation("WriteDataToOutput", args);
}
public void WriteErrorToOutput(string data)
{
    var args = new object[]
    {
        data
    };
    InvokePresentation("WriteErrorToOutput", args);
}
}}
