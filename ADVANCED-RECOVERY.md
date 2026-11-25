# REAlity Advanced Recovery Lab

Open `advanced.html` from the main REAlity web interface. The UI is available without desktop installation. The Pages build stages optional engines and emits `vendor/status.json`; the UI disables unavailable engines instead of claiming they work.

## Native machine-code WASM decompiler

`native-wasm` is a wasm-bindgen wrapper around Craft Anything's actual Rust disassembly and pseudo-C engine, pinned at v0.6.1 commit 48a9c5a60ff83ff620f98661339be6281a7debc6. The Pages workflow builds for wasm32-unknown-unknown and runs a known x86 function fixture first. The web worker supports cancellation, pagination, and JSON evidence export.

Supported container/architecture combinations are those the upstream parser and decoder accept. Native analysis has explicit bounds (64 MiB input, 2,000 functions, 400,000 total decoded instructions, 32 functions per requested page in the UI). The output contains function addresses, control-flow blocks, calls, inferred pseudo-C and limitations. This is not exact original source. Managed .NET IL, Java bytecode and Python bytecode need their own decompilers. Obfuscated, packed, unsupported or heavily optimized binaries can be incomplete. No original native binary is executed during this analysis.

The optional upstream Craft Anything viewer is staged independently with upstream release checksums. Engine availability depends on a successful CI build and actual browser support. Test native results against known originals.

## Browser virtual PC

The pinned v86 x86 emulator runs locally via WASM with SeaBIOS/VGABIOS. It accepts user-provided compatible bootable raw disks, ISOs or floppy images (512 MiB input limit). No Windows installation image or license is distributed. Older 32-bit Windows versions and ReactOS may boot; modern 64-bit Windows is unsupported. OS boot and application compatibility are not guaranteed. No network relay is configured; the emulator is not a hardened sandbox. Do not run unknown or malicious binaries.

Boot the guest, then insert an original EXE and companion files as a virtual data CD (flat, up to 20 files / 128 MiB); use a prepared ISO for larger directory structures. Launch the original inside the guest. Capture a graphical screen or replay a bounded keyboard trace using JSON, with named screenshot checkpoints. Guest interaction and OS state remain target-specific. Example:

```json
{"steps":[{"op":"wait","ms":1000},{"op":"snapshot","name":"initial"},{"op":"text","value":"hello"},{"op":"wait","ms":1000},{"op":"snapshot","name":"entered"}]}
```

Modern Windows applications require separately provisioned, licensed, isolated x64 Windows VM infrastructure with remote browser access; none has been provisioned by this repository.

## Runtime comparison

The advanced lab compares same-sized screenshots and produces pixel difference masks, tolerance-dependent changed-pixel metrics, and JSON. It also compares all matching PNG checkpoints from two trace ZIPs. Screenshot comparison alone does not establish functional equivalence. Supply equivalent guest state and rebuilt web state and matching names; missing/different-size checkpoints are reported.

For two browser-compatible sites, `scripts/compare-runtime.mjs` performs real Chromium interactions using declared cases, compares observable text/value/visibility assertions and errors at three viewport sizes, captures screenshots and produces difference images. The runner routes only static files from the selected site root, denies external requests, and enables Chromium's sandbox. Run it only inside a dedicated disposable, network-restricted environment with resource limits. Do not give it GitHub credentials, secrets, or access to other data. The CI workflow uses only known repository fixtures. It does not run arbitrary native Windows programs.

```sh
npm install --ignore-scripts
npx playwright install --with-deps chromium
node scripts/compare-runtime.mjs tests/fixtures/runtime-original tests/fixtures/runtime-rebuilt tests/fixtures/runtime-cases.json runtime-evidence
```

A remote service could expose this runner through HTTPS without a desktop install; such compute is not deployed. Native screenshot replays and web interaction assertions do not automatically infer a complete equivalence test suite from an unknown EXE.

## Verification and deployment

Use GitHub Actions' Pages workflow. It stages pinned upstream engines, runs browser module tests and compiles the Rust wrapper. Engine staging failures are reported in vendor/status.json. A separate runtime-validation workflow tests the interaction comparison on trusted fixtures and uploads evidence. Run both and inspect logs; no live build or test pass is asserted solely from committing source.

Source: Craft Anything (MIT/Apache-2.0), v86 (BSD-2-Clause), associated firmware upstream licenses. Third-party engine artifacts are staged in CI, not checked in as unverified binaries.
