"""Port of the original vtkControl/vtkMax/Widget/02_vtkMaxScaleWidget.cs.

A 400 px scale bar with five alternating fields, "nice" model-length labels
(format G4) and the model length unit on the last label, horizontally placed at
320 px from the left at the bottom, keeping its relative centre when the window
is resized (vtkMaxBorderWidget.HorizontallyRelative).
"""
import math

from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
from vtkmodules.vtkRenderingCore import vtkActor2D, vtkPolyDataMapper2D, vtkTextActor


def format_g4(value):
    """.NET ToString("G4"): four significant digits, no trailing zeros."""
    if value == 0:
        return '0'
    text = f'{value:.4g}'
    if 'e' in text:
        mantissa, exponent = text.split('e')
        sign = exponent[0]
        digits = exponent[1:].lstrip('0').rjust(2, '0')
        text = f'{mantissa}E{sign}{digits}'
    return text


class OriginalScaleWidget:
    FIELDS = 5

    def __init__(self, renderer, width=400, x=320, y=0, padding=5, bar_height=10):
        self.renderer = renderer
        self.width = float(width)
        self.bar_width = self.width
        self.bar_height = bar_height
        self.padding = padding
        self.position = [float(x), float(y)]
        self.unit = ''
        self.visible = True
        self.previous_size = None
        self.size = [0.0, 0.0]
        self.labels = []
        for _ in range(self.FIELDS + 1):
            label = vtkTextActor()
            prop = label.GetTextProperty()
            prop.SetColor(0, 0, 0)
            prop.SetFontFamilyToArial()
            prop.SetFontSize(16)
            prop.SetLineOffset(-round(16 / 7.0))
            prop.SetLineSpacing(1.5)
            label.GetPositionCoordinate().SetCoordinateSystemToDisplay()
            self.labels.append(label)
        self.points = vtkPoints()
        self.polygons = vtkCellArray()
        self.lines = vtkCellArray()
        fill = vtkPolyData()
        fill.SetPoints(self.points)
        fill.SetPolys(self.polygons)
        border = vtkPolyData()
        border.SetPoints(self.points)
        border.SetLines(self.lines)
        self.fill_data, self.border_data = fill, border
        self.fill_actor, self.border_actor = vtkActor2D(), vtkActor2D()
        for actor, data in ((self.fill_actor, fill), (self.border_actor, border)):
            mapper = vtkPolyDataMapper2D()
            mapper.SetInputData(data)
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0, 0, 0)
        self.attach()
        renderer.AddObserver('StartEvent', lambda *_: self.update())

    def attach(self):
        for actor in self.actors():
            self.renderer.AddActor2D(actor)

    def actors(self):
        return [self.fill_actor, self.border_actor] + self.labels

    def set_unit(self, unit):
        self.unit = unit or ''

    def set_visibility(self, visible):
        self.visible = bool(visible)
        for actor in self.actors():
            actor.SetVisibility(self.visible)

    def _text_size(self, label):
        bbox = [0.0, 0.0, 0.0, 0.0]
        label.GetBoundingBox(self.renderer, bbox)
        return bbox[1] - bbox[0], bbox[3] - bbox[2]

    def _relative_position(self):
        size = self.renderer.GetSize()
        # The original starts tracking at the control's real size; ignore the transient
        # tiny sizes a native view reports before it is laid out.
        if size[0] < 2 * self.width:
            return
        if self.previous_size and tuple(size) != self.previous_size:
            centre = (self.position[0] + self.size[0] / 2) / self.previous_size[0]
            self.position[0] = size[0] * centre - self.size[0] / 2
        self.previous_size = tuple(size)
        self.position[0] = min(max(self.position[0], 0.0), max(size[0] - self.size[0], 0.0))

    def update(self):
        if not self.visible or self.renderer.GetSize()[0] == 0:
            return
        self._relative_position()
        renderer = self.renderer
        renderer.SetDisplayPoint(0, 0, 0)
        renderer.DisplayToWorld()
        first = renderer.GetWorldPoint()
        renderer.SetDisplayPoint(0, self.width, 0)
        renderer.DisplayToWorld()
        second = renderer.GetWorldPoint()
        if first[3] and second[3]:
            first = [v / first[3] for v in first[:3]]
            second = [v / second[3] for v in second[:3]]
        length = math.dist(first[:3], second[:3])
        model_width = 0.0
        if length and not math.isnan(length):
            previous = self.bar_width
            p = math.floor(math.log10(length))
            scaled = length / 10 ** p
            ratio = round(5 * scaled) / 5 / scaled
            self.bar_width = self.width * ratio
            model_width = round(5 * scaled) / 5 * 10 ** p
            self.position[0] -= (self.bar_width - previous) / 2
        step = model_width / self.FIELDS
        for i, label in enumerate(self.labels):
            label.SetInput(format_g4(i * step))
        if self.unit:
            self.labels[-1].SetInput(self.labels[-1].GetInput() + ' ' + self.unit)
        first_w, first_h = self._text_size(self.labels[0])
        x0 = self.position[0] + first_w / 2 + self.padding
        y0 = self.position[1] + first_h + 2 * self.padding
        dx = self.bar_width / self.FIELDS
        self.points.SetNumberOfPoints(2 * (self.FIELDS + 1))
        for i in range(self.FIELDS + 1):
            self.points.SetPoint(2 * i, x0 + i * dx, y0, 0)
            self.points.SetPoint(2 * i + 1, x0 + i * dx, y0 + self.bar_height, 0)
        self.polygons.Reset()
        for i in range(0, self.FIELDS, 2):
            self.polygons.InsertNextCell(4)
            for index in (2 * i, 2 * (i + 1), 2 * (i + 1) + 1, 2 * i + 1):
                self.polygons.InsertCellPoint(index)
        self.lines.Reset()
        for i in range(self.FIELDS + 1):
            self.lines.InsertNextCell(2)
            self.lines.InsertCellPoint(2 * i)
            self.lines.InsertCellPoint(2 * i + 1)
        for a, b in ((0, 2 * self.FIELDS), (1, 2 * self.FIELDS + 1)):
            self.lines.InsertNextCell(2)
            self.lines.InsertCellPoint(a)
            self.lines.InsertCellPoint(b)
        self.points.Modified()
        self.fill_data.Modified()
        self.border_data.Modified()
        for i, label in enumerate(self.labels):
            w, _ = self._text_size(label)
            point = self.points.GetPoint(2 * i)
            label.SetPosition(point[0] - w / 2, self.position[1] + self.padding)
        last_w, last_h = self._text_size(self.labels[-1])
        self.size = [self.padding + first_w / 2 + self.bar_width + last_w / 2 + self.padding,
                     4 * self.padding + last_h + self.bar_height + first_h]
