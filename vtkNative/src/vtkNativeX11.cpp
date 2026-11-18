// PrePoMax - Copyright (C) 2016-2026 Matej Borovinsek
// An embedded view on X11 (Linux). VTK's interactor selects the mouse and the keys on its own window inside the
// parent (vtkXRenderWindowInteractor::Enable), so the host toolkit never sees them, and fires its timers only from
// its own event loop. As with a Cocoa view, the parent takes the input and hands it to vtkn_view_handle_input; the
// host pumps VTK's display connection (exposure, size and the interaction style's timers) with
// vtkn_view_process_events.
#include "vtkNativeX11.h"

#if defined(VTKNATIVE_X11)

#include <vtkRenderWindow.h>
#include <vtkRenderWindowInteractor.h>

#include <cstdint>

// Xlib last: its macros (None, Status, Bool) collide with VTK names
#include <X11/Xlib.h>

namespace vtkn
{
    void X11LeaveInputToParent(vtkRenderWindow* renderWindow)
    {
        Display* display = static_cast<Display*>(renderWindow->GetGenericDisplayId());
        Window window = static_cast<Window>(reinterpret_cast<std::uintptr_t>(renderWindow->GetGenericWindowId()));
        if (display == nullptr || window == 0) return;
        // Unselected events propagate to the parent window (the host's)
        XSelectInput(display, window, ExposureMask | StructureNotifyMask);
        XFlush(display);
    }

    void X11ProcessEvents(vtkRenderWindowInteractor* interactor)
    {
        if (interactor != nullptr && interactor->GetInitialized()) interactor->ProcessEvents();
    }
}

#else

namespace vtkn
{
    // Win32 and Cocoa views get their exposure and timers from the message loop of the host
    void X11LeaveInputToParent(vtkRenderWindow*) {}
    void X11ProcessEvents(vtkRenderWindowInteractor*) {}
}

#endif
