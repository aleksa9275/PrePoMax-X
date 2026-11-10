"""Probe helper: operates the visible original form through the same control-model inputs the renderer
uses for user actions (list click, property edit, button click) and captures original message boxes."""
from System import Array, Int32
from System.Windows.Forms import PropertyGrid, ListView, GridItemType, Button


def walk(control):
    for child in control.Controls:
        yield child
        yield from walk(child)


def visible(text):
    return str(text or '').lstrip('​\t')


class FormDriver:
    def __init__(self, window):
        self.window = window
        self.host = window.form_host
        self.renderer = window.form_renderer
        if getattr(window, 'auto_prompts', None) is None:
            window.auto_prompts = []

    @property
    def form(self):
        return self.host.ActiveItemForm

    @property
    def prompts(self):
        return self.window.auto_prompts

    def control(self, name, form=None):
        return next(c for c in walk(form or self.form) if str(c.Name) == name)

    @property
    def grid(self):
        return next(c for c in walk(self.form) if isinstance(c, PropertyGrid))

    @property
    def types(self):
        view = next((c for c in walk(self.form) if isinstance(c, ListView) and str(c.Name) == 'lvTypes'), None)
        return [] if view is None else [str(i.Text) for i in view.Items]

    def select_type(self, text):
        view = self.control('lvTypes')
        index = [str(i.Text) for i in view.Items].index(text)
        self.renderer.guard(lambda: view.SelectByUser(Array[Int32]([index])))
        self.flush()

    def row(self, label):
        for item in PropertyGrid.Flatten(self.grid.Root):
            if item.GridItemType == GridItemType.Property and (visible(item.Label) == label or str(item.PropertyDescriptor.Name) == label):
                return item
        raise KeyError('No property row ' + label + ' in ' + ', '.join(self.labels()))

    def set_choice(self, label, text):
        """Picks the drop-down value containing text (case-insensitive) as a user would."""
        choices = self.choices(label)
        found = [v for v in choices if text.lower() in v.lower()]
        if not found:
            raise AssertionError('choice ' + text + ' not offered for ' + label + ': ' + ', '.join(choices))
        self.set(label, found[0])

    def labels(self):
        return [visible(i.Label) for i in PropertyGrid.Flatten(self.grid.Root) if i.GridItemType == GridItemType.Property]

    def has(self, label):
        try:
            self.row(label)
            return True
        except KeyError:
            return False

    def get(self, label):
        return str(self.grid.GetText(self.row(label)))

    def set(self, label, text):
        """A committed grid edit (WinForms PropertyGrid: value set, then PropertyValueChanged)."""
        grid, row = self.grid, self.row(label)
        self.renderer.guard(lambda: grid.SetValueFromText(row, str(text)))
        self.flush()

    def choices(self, label):
        exclusive = False
        values, exclusive = self.grid.GetStandardValues(self.row(label), exclusive)
        return [str(v) for v in values]

    def click(self, name, form=None):
        control = self.control(name, form)
        self.renderer.guard(control.RaiseClick)
        self.flush()

    def ok(self):
        self.click('btnOK')

    def ok_new(self):
        self.click('btnOkAddNew')

    def cancel(self):
        self.click('btnCancel')

    def flush(self):
        self.renderer.flush()
        from PyQt6 import QtWidgets
        QtWidgets.QApplication.processEvents()
        self.renderer.flush()
