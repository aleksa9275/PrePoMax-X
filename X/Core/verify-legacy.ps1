param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskOutput = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $taskOutput -Force | Out-Null
$taskSdk = (& dotnet --version).Trim()
$taskSdkLine = & dotnet --list-sdks | Where-Object { $_.StartsWith("$taskSdk [") }
if (@($taskSdkLine).Count -ne 1) { throw 'Could not identify the selected SDK compiler' }
$taskSdkRoot = $taskSdkLine.Substring($taskSdkLine.IndexOf('[') + 1).TrimEnd(']')
$taskCompiler = Join-Path $taskSdkRoot "$taskSdk/Roslyn/bincore/csc.dll"
$taskFramework = Join-Path $env:SystemRoot 'Microsoft.NET/Framework64/v4.0.30319'
if (!(Test-Path -LiteralPath $taskFramework)) { throw 'Native Windows x64 .NET Framework runtime is required' }
$taskReferences = @('mscorlib.dll','System.dll','System.Core.dll','System.Drawing.dll','System.Xml.dll','System.Xml.Linq.dll') |
    ForEach-Object { "/reference:$(Join-Path $taskFramework $_)" }
$taskGlobals = @('CaeGlobals/Properties/AssemblyInfo.cs','CaeGlobals/CaeException.cs',
    'CaeGlobals/CommonClasses/Vec3D.cs','CaeGlobals/CommonClasses/Matrix.cs') |
    ForEach-Object { Join-Path $taskRoot $_ }
$taskMesh = @('CaeMesh/Properties/AssemblyInfo.cs','CaeMesh/Nodes/FeNode.cs',
    'CaeMesh/Meshing/Transfinite/TransfiniteSideTriple.cs','CaeMesh/Meshing/Transfinite/ThreeBlockGrid.cs',
    'CaeMesh/Meshing/Transfinite/ThreeBlockMapping.cs') | ForEach-Object { Join-Path $taskRoot $_ }
& dotnet $taskCompiler /nologo /noconfig /nostdlib+ /target:library "/out:$taskOutput/CaeGlobals.dll" @taskReferences @taskGlobals
if ($LASTEXITCODE -ne 0) { throw 'Legacy globals slice compilation failed' }
& dotnet $taskCompiler /nologo /noconfig /nostdlib+ /target:library "/out:$taskOutput/CaeMesh.dll" @taskReferences "/reference:$taskOutput/CaeGlobals.dll" @taskMesh
if ($LASTEXITCODE -ne 0) { throw 'Legacy mesh slice compilation failed' }
& dotnet $taskCompiler /nologo /noconfig /nostdlib+ /target:exe "/out:$taskOutput/Smoke.exe" @taskReferences "/reference:$taskOutput/CaeGlobals.dll" "/reference:$taskOutput/CaeMesh.dll" (Join-Path $PSScriptRoot 'Tests/Legacy/Smoke.cs')
if ($LASTEXITCODE -ne 0) { throw 'Legacy smoke host compilation failed' }
$taskResult = & (Join-Path $taskOutput 'Smoke.exe')
if ($LASTEXITCODE -ne 0) { throw 'Legacy smoke execution failed' }
$taskReport = [ordered]@{
    success = $true
    scope = 'Shared source slice compiled against installed .NET Framework runtime assemblies; not full Windows solution'
    sdk = $taskSdk
    smoke = ($taskResult | ConvertFrom-Json)
    compilerSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $taskCompiler).Hash.ToLowerInvariant()
    assemblyHashes = @{}
}
foreach ($taskName in @('CaeGlobals.dll','CaeMesh.dll','Smoke.exe')) {
    $taskReport.assemblyHashes[$taskName] = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $taskOutput $taskName)).Hash.ToLowerInvariant()
}
$taskReport | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 -LiteralPath (Join-Path $taskOutput 'verification.json')
$taskResult
