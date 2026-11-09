using CaeGlobals;using CaeResults;using PrePoMax;using PrePoMax.Forms;using PrePoMax.Settings;
namespace PrePoMaxX.UI;
public sealed class PresentationEditSession(Controller controller,string family)
{
 readonly object value=family switch{
  "Legend"=>new ViewLegendSettings(controller.Settings.Legend.DeepClone()),
  "Postprocessing"=>new ViewPostSettings(controller.Settings.Post.DeepClone()),
  "Annotations"=>new ViewAnnotationSettings(controller.Settings.Annotations.DeepClone()),
  "Status block"=>new ViewStatusBlockSettings(controller.Settings.StatusBlock.DeepClone()),
  "Number format"=>new ViewNumberFormatSettings(controller.Settings.NumberFormat.DeepClone()),
  "Section view"=>CreateSection(controller),
  "Exploded view"=>new ViewExplodedViewParameters {Parameters=(controller.GetCurrentExplodedViewParameters()??new ExplodedViewParameters()).DeepClone()},
  _=>throw new NotSupportedException(family)};
 public PropertySheet Properties=>new(value,changed:()=>value.GetType().GetMethod("UpdateVisibility",Type.EmptyTypes)?.Invoke(value,null));
 static SectionViewParameters CreateSection(Controller c){var plane=c.GetSectionViewPlane();return new SectionViewParameters{Point=plane?.Point.Coor??c.GetSectionViewBBCenter().Coor,Normal=plane?.Normal.Coor??c.GetDefaultSectionViewNormal()};}
 public void Apply()
 {
  if(value is SectionViewParameters section)controller.CreateSectionView(section.Point,section.Normal,section.LightenColors,section.SectionColor,section.ElementWise,section.Hatch);
  else if(value is ViewExplodedViewParameters exploded)controller.ApplyExplodedView(exploded.Parameters);
  else {
   var settings=controller.Settings;
   switch(value){case ViewLegendSettings legend:settings.Legend=(LegendSettings)legend.GetBase();break;
    case ViewPostSettings post:settings.Post=(PostSettings)post.GetBase();break;
    case ViewAnnotationSettings annotation:settings.Annotations=(AnnotationSettings)annotation.GetBase();break;
    case ViewStatusBlockSettings status:settings.StatusBlock=(StatusBlockSettings)status.GetBase();break;
    case ViewNumberFormatSettings format:settings.NumberFormat=(NumberFormatSettings)format.GetBase();break;}
   controller.Settings=settings;controller.Redraw();
  }
 }
}
