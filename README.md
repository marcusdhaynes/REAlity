# REAlity — Recovery Workbench

Local-first recovery of your own lost software source. Import an executable, installer, archive or complete installation folder. Original bytes are preserved with SHA-256; static inspection is the default. No AI or network is required for the built-in engine.

## Run
Python 3.10+ with Tkinter: double-click Launch-REAlity.cmd on Windows, or run python desktop.py. CLI: python recovery.py TARGET NEW_WORKSPACE. Use --doctor to check optional providers, --external to opt into installed tools.

## Optional engines
- REA: https://github.com/morluto/rea (npm package rea-agents; run setup and configure Ghidra).
- Ghidra: https://github.com/NationalSecurityAgency/ghidra
- ILSpy CLI: https://github.com/icsharpcode/ILSpy (dotnet tool install -g ilspycmd).
- Electron ASAR: https://github.com/electron/asar
- JADX: https://github.com/skylot/jadx
- Detect It Easy: https://github.com/horsicq/Detect-It-Easy
- PyInstaller extractor: https://github.com/pyinstxtractor/pyinstxtractor-ng
- Craft Anything: https://github.com/storytold/craft-anything (optional independent reconstruction workflow; use Deep mode for your own software).

Install only trusted official releases. Provider executables must be on PATH; Windows .cmd shims are not invoked by the engine. External tools process copies and are not sandboxed by REAlity. Keep unknown applications in an isolated VM. The application never launches the target itself. AI-assisted rebuilding is not implemented in this version; Craft Anything can be opened separately.

## Output
Original / Extracted / Source / Assets / Dependencies / Analysis / Reconstructed / Tests.
Analysis/report.json is evidence, not a claim of full recovery. Source files include copied candidates and decompiler output; they are not necessarily buildable. Reconstructed/RECOVERY_TASK.md describes a follow-up reconstruction and validation process. The native REA adapter produces overview evidence, not original source. Missing tools and errors are recorded, not concealed.

## Development
python -m unittest -v
GitHub Actions runs tests and builds a Windows executable with PyInstaller. Build artifacts are available from successful workflow runs. No release is claimed until CI succeeds.

## Roadmap
Full native decompilation orchestration, recursive installer and ASAR extraction, PDB/source-map recovery, build manifest reconstruction, optional coding-agent integration, isolated behavior comparison, and portable cross-platform releases. Preserve recovered vs inferred provenance and do not label generated code as original.
