using System;
using System.IO;
using System.Reflection;
using CaeGlobals;
using CaeModel;
using PrePoMaxX.Persistence;
namespace PrePoMax
{
    /// <summary>Original PMX/settings reading with the explicit type allowlist (never unrestricted deserialization),
    /// the code pages and culture of the original start-up.</summary>
    public static class OriginalPersistence
    {
        static readonly Lazy<NrbfTypePolicy> policy=new(CreatePolicy);
        public static void Install()
        {
            System.Text.Encoding.RegisterProvider(System.Text.CodePagesEncodingProvider.Instance);
            RuntimeInitialization.SetCultureAndLanguage();
            BinarySerialization.Factory=()=>new RestrictedNrbfSerializer(policy.Value);
        }
        static NrbfTypePolicy CreatePolicy()
        {
            Assembly[] assemblies={typeof(Controller).Assembly,typeof(FeModel).Assembly,typeof(CaeMesh.FeMesh).Assembly,typeof(CaeResults.FeResults).Assembly,typeof(CaeJob.AnalysisJob).Assembly,typeof(NamedClass).Assembly,typeof(vtkControl.vtkMaxActorData).Assembly,typeof(UserControls.SidePanelsState).Assembly,typeof(System.Windows.Forms.DialogResult).Assembly};
            using var resource=typeof(OriginalPersistence).Assembly.GetManifestResourceStream("PrePoMaxX.AllowedTypes");
            using var reader=new StreamReader(resource);
            return new NrbfTypePolicy(assemblies,reader.ReadToEnd().Split(new[]{'\r','\n'},StringSplitOptions.RemoveEmptyEntries));
        }
    }
}
