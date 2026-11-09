"""Native VTK mapping of original scalar data and original color-spectrum settings."""
from vtkmodules.vtkCommonCore import vtkLookupTable
from vtkmodules.vtkRenderingCore import vtkColorTransferFunction
from original_colormaps import COLORMAPS

def lookup(spectrum,low,high):
    ctf=vtkColorTransferFunction()
    spec=COLORMAPS[str(spectrum.Type)]
    getattr(ctf,'SetColorSpaceTo'+spec['space'])()
    for x,*rgb in spec['points']:
        ctf.AddRGBPoint(1-x if spectrum.ReverseColors else x,*[v+float(spectrum.ColorBrightness)*(1-v) for v in rgb])
    count=256 if str(spectrum.Mode)=='Smooth' else spectrum.NumberOfColors
    # Same manual bounds / extra endpoint-color bins as PrepareActorLookupTable.
    below=above=False
    if str(spectrum.MinMaxType)=='Manual':
        low=min(low,spectrum.MinUserValue);high=max(high,spectrum.MaxUserValue)
        below=spectrum.MinUserValue>low and high!=low
        above=spectrum.MaxUserValue<high and high!=low
        if below:low=spectrum.MinUserValue
        if above:high=spectrum.MaxUserValue
    delta=(high-low)/count
    table=vtkLookupTable();table.SetTableRange(low-delta if below else low,high+delta if above else high)
    table.SetNumberOfTableValues(count+int(below)+int(above));table.Build()
    def rgba(c):return c.R/255,c.G/255,c.B/255,1
    index=0
    if below:table.SetTableValue(index,*rgba(spectrum.MinColor));index+=1
    for i in range(count):table.SetTableValue(index+i,*ctf.GetColor(i/(count-1)),1)
    if above:table.SetTableValue(index+count,*rgba(spectrum.MaxColor))
    table.SetNanColor(.5,.5,.5,1)
    return table
