# Remove the local preview and reset tests

A DMG is a disk-image file. Opening it mounts a volume; dragging the app out
creates a separate installed copy. Deleting the DMG does not remove that copy.
No privileged installer, launch agent, login item or background service is added.
Do these steps yourself when you want to reset; none are run automatically.

## 1. Stop and remove the application

- In the app, cancel any active job and wait for **Cancelled** or **Completed**,
  then quit. Closing during a job also requests cancellation and waits for cleanup.
- Eject **PrePoMax-X Preview** in Finder if the image is still mounted. Eject each
  mounted preview volume if you opened several builds.
- Move **PrePoMax-X-Viewport.app** from `/Applications` to Trash. Also remove any
  copies you made in `~/Applications`, Desktop, Downloads or another test folder.
  Removing one copy does not remove the others.

## 2. Remove this preview's per-user state

First keep any solver results you want. **Job files** in the running app reveals
its exact job location. In Finder use **Go → Go to Folder…** for the paths below.
Move only the indicated preview-specific items to Trash, if they exist:

| Location | What it contains |
|---|---|
| `~/Library/Application Support/PrePoMax-X/PrePoMax-X Preview/` | Default job folders, including generated decks, FRD/DAT results, output/error logs and job JSON |
| `~/Library/Caches/PrePoMax-X/PrePoMax-X Preview/` | Preview-specific cache, if created |
| `~/Library/Preferences/PrePoMax-X/PrePoMax-X Preview/` | Qt preview configuration directory, if created |
| `~/Library/Preferences/com.prepomax-x.PrePoMax-X Preview.plist` | Qt settings file, if created; current app does not deliberately save settings |
| `~/Library/Preferences/org.prepomaxx.preview.plist` | macOS preferences for this preview, if created |
| `~/Library/Saved Application State/org.prepomaxx.preview.savedState/` | macOS saved window state, if created |

The first local development packages used bundle ID `PrePoMax-X-Viewport`.
If you tested those intermediate builds, also remove their exact
`~/Library/Preferences/PrePoMax-X-Viewport.plist` and
`~/Library/Saved Application State/PrePoMax-X-Viewport.savedState/`, if present.

Do not delete the whole `~/Library/Preferences`, `Caches`, or parent project-data
folder. If you passed `--jobs-root`, those jobs are in your chosen directory,
not the default above. Our automated copied-app tests use `Job workspace` inside
the corresponding verification output folder in step 3.

## 3. Remove DMGs and generated development/test copies

- Move the specific `PrePoMax-X-Preview-arm64.dmg` files you no longer need to
  Trash, including duplicates in Downloads or other copied locations.
- For this checkout, generated task 0042 files are under
  `/Users/aleksa/Documents/GitLab/pre-po-max-x/X/Build/artifacts/`.
  The folders beginning `task0042-` contain package outputs, build caches, staged
  app copies, test installations, generated jobs, screenshots and DMGs. After
  preserving wanted results/evidence and ejecting their volumes, move the specific
  task 0042 folders you want to reset to Trash. This includes failed packaging
  attempts (`task0042-macos-preview`, `-r2`, `-r3`) and the final package/test folders.
- The corresponding check outputs are under
  `X/Checks/artifacts/task0042-execution-macos*` within this checkout. They may also
  be removed when their diagnostic evidence is no longer needed.
- Earlier task 0037/0041 generated app bundles remain in their own ignored
  `X/Desktop/artifacts/` or `X/Build/artifacts/` directories. Remove those specific
  output folders too if you want no older development copies on disk.

Keep the tracked source tree and `.project/reports/`: they hold build instructions
and bug evidence, not an installed app. Build-only environments such as
`/private/tmp/prepomaxx-desktop-runtime` and Homebrew are not installed by the DMG
and do not affect a normal user installation. They can remain for rebuilding.
User models or results saved outside these generated locations are yours; remove
or retain those explicitly rather than treating them as disposable cache.

Optional: if a test crashed, Finder's `~/Library/Logs/DiagnosticReports/` may
contain files whose names start `PrePoMax-X-Viewport`. Remove only the matching
reports you no longer need. Do not clear unrelated diagnostics or system logs.

## 4. Verify a fresh test

After the above, the app is absent from your chosen install folders, no preview
volume is mounted, and the listed preview-specific state folders are absent.
Use a newly copied app and a fresh job directory for the next test. You do not
need to empty the entire Trash to reset application state; remove only the
preview items permanently if reclaiming their disk space is also your goal.

This resets this application's files and per-user state. It does not turn your
Mac into a clean OS or erase macOS trust/launch history. For a true clean-install
or downloaded Gatekeeper test, use a fresh macOS account/VM or second Mac and
record that environment. Apple's Linux containers cannot run this macOS GUI.
There is no need to disable Gatekeeper, delete quarantine attributes or reset
system security databases for uninstalling or testing this preview.
