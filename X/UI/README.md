# The original forms on the WinForms control model

This folder holds what the original application (`X/App`) compiles its forms against. Since M3-1b it has no
user interface of its own. The PyQt6 workbench (the C1–C12 and M1–M2 renderer, `OriginalFormHost`/`OriginalViewHost`,
the Qt GUI probes and generators) was retired with PyQt (D065). Its successor is the Avalonia front end in
`X/App/FrontEnd`, whose checks are `X/App/verify-app.py` (check area `app`). The removed files are in git history
before the M3-1b commit.

| Path | What it is |
|---|---|
| `FormsCompat/` | the headless WinForms control model (`System.Windows.Forms` types, the dotnet/winforms layout engines) the original forms and FrmMain run on |
| `generate-original-forms.py` | copies the original form classes (class, designer partial, base forms) into `Workbench/OriginalForms/` and `X/App/Original/` with the reviewed rewrites only; `--check` fails when an original changed or an output was edited |
| `FormSourceGen/` | the Roslyn extractor the generator uses |
| `Workbench/OriginalForms/` | the generated original form classes; `X/App/PrePoMax` and `X/App/UserControls` compile them (the folder keeps its name until the organization pass in M5) |
| `fixtures/` | small public test inputs (`cube.brep` for the geometry probe area) |

Check the generated classes:

```sh
dotnet build X/UI/FormSourceGen/FormSourceGen.csproj -c Release
python3 X/UI/generate-original-forms.py --check
```
