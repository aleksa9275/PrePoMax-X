// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
// Licensed under the terms defined in the root LICENSE file.
using System;
using System.Collections.Generic;
using CaeGlobals;
using CaeModel;
using PrePoMax.PropertyViews;
namespace PrePoMax
{
    public static class SurfaceInteractionEditor
    {
        public static ViewSurfaceInteractionProperty CreateView(SurfaceInteractionProperty property)
        {
            if(property is SurfaceBehavior sb)return new ViewSurfaceBehavior(sb);
            if(property is Friction fr)return new ViewFriction(fr);
            if(property is GapConductance gc)return new ViewGapConductance(gc);
            throw new NotSupportedException();
        }
        public static SurfaceInteraction Build(string name,IEnumerable<ViewSurfaceInteractionProperty> views)
        {
            Friction friction = null;
            SurfaceBehavior surfaceBehavior = null;
            SurfaceInteraction interaction = new SurfaceInteraction(name);
            foreach (ViewSurfaceInteractionProperty view in views)
            {
                interaction.AddProperty(view.Base);
                if (view is ViewSurfaceBehavior vsb) surfaceBehavior = (SurfaceBehavior)vsb.Base;
                if (view is ViewFriction vf) friction = (Friction)vf.Base;
            }
            if (surfaceBehavior == null)
                throw new CaeException("Surface interaction must define a surface behavior.");
            // Tied contact requires friction definition
            if (surfaceBehavior != null && surfaceBehavior.PressureOverclosureType == PressureOverclosureEnum.Tied
                && friction == null)
            {
                throw new CaeException("A tied contact requires a stick slope definition using the friction interaction model. " +
                                       "The value of the friction coefficient is irrelevant for tied contact.");
            }
            return interaction;
        }
    }
}
