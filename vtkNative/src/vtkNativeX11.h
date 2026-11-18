// PrePoMax - Copyright (C) 2016-2026 Matej Borovinsek
#pragma once

class vtkRenderWindow;
class vtkRenderWindowInteractor;

namespace vtkn
{
    // X11: VTK's window inside the parent leaves the mouse and the keys to the parent (no-op elsewhere)
    void X11LeaveInputToParent(vtkRenderWindow* renderWindow);
    // X11: dispatches the pending events of VTK's display connection and fires due timers (no-op elsewhere)
    void X11ProcessEvents(vtkRenderWindowInteractor* interactor);
}
