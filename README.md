# REAlity — Recovery Workbench

Local-first recovery of your own lost software source. Import an executable, installer, archive or complete installation folder. Original bytes are preserved with SHA-256; static inspection is the default. No AI or network is required for the built-in engine.

## Run
Python 3.10+ with Tkinter: double-click Launch-REAlity.cmd on Windows, or run python desktop.py. CLI: python recovery.py TARGET NEW_WORKSPACE. Use --doctor to check optional providers, --external to opt into installed tools.

The original standalone offline browser analyzer is preserved in REAlity-Offline.html and is accessible from the desktop workbench.

## Built-in offline extraction
Packed Electron ASAR files are parsed directly without npm or AI. Nested archives and ASAR contents are recursively organized within the extraction limits. Version 3 source maps (including embedded indexed sections) recover their original embedded sourcesContent text into Source with hashes and source-name provenance. Missing or external source entries are recorded, not downloaded. Linked and unpacked ASAR entries are skipped; include the entire installation directory to preserve companion files.

## Optional engines
- REA: https://github.com/morluto/rea (npm package rea-agents; run setup and configure Ghidra).
- Ghidra: https://github.com/NationalSecurityAgency/ghidra
- ILSpy CLI: https://github.com/icsharpcode/ILSpy (dotnet tool install -g ilspycmd).
- Electron ASAR: https://github.com/electron/asar
- JADX: https://github.com/skylot/jadx
- Detect It Easy: https://github.com/horsicq/Detect-It-Easy
- PyInstaller extractor: https://github.com/pyinstxtractor/pyinstxtractor-ng
- Craft Anything: https://github.com/storytold/craft-anything (optional independent reconstruction workflow; use Deep mode for your own software).

Install only trusted official releases. Provider executables must be on PATH; Known REA and ASAR npm shims on Windows resolve to their installed Node entry point; other shell wrappers are not invoked by the engine. External tools process copies and are not sandboxed by REAlity. Keep unknown applications in an isolated VM. The application never launches the target itself. After static recovery, select **Reconstruct** to prepare a Craft Anything Deep-mode rebuild using the preserved target and recovery evidence. Install Craft Anything CLI and configure a supported coding agent first. Windows opens an interactive terminal; other platforms copy the command for a terminal. A separate Reconstructed/CraftProject folder receives the result. No unattended approval is enabled. The agent may execute code or transmit evidence under its own permissions; use an isolated VM and no production credentials. This is an optional integration, not verified behavioral equivalence.

## Output
Original / Extracted / Source / Assets / Dependencies / Analysis / Reconstructed / Tests.
Analysis/report.json is evidence, not a claim of full recovery. Source files include copied candidates and decompiler output; they are not necessarily buildable. Reconstructed/RECOVERY_TASK.md describes a follow-up reconstruction and validation process. The native REA adapter produces overview evidence, not original source. Missing tools and errors are recorded, not concealed.

## Development
python -m unittest -v
GitHub Actions runs tests and builds a Windows executable with PyInstaller. Successful main-branch builds publish versioned Windows preview executables under GitHub Releases and retain the Actions build artifact. No release is claimed until CI succeeds.

## Roadmap
Full native decompilation orchestration, recursive installer extraction, PDB and additional source-map formats, build manifest reconstruction, live provider and coding-agent validation, isolated behavior comparison, and portable cross-platform releases. Preserve recovered vs inferred provenance and do not label generated code as original.
