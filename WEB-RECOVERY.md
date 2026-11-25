# REAlity Web recovery and publishing

The Pages frontend runs without a desktop install. All static analysis and export happen in the browser by default. A separately hosted service is required for AI reconstruction of native software. Neither Pages nor the browser can run an arbitrary Windows EXE natively.

## Local web workflow

Open https://marcusdhaynes.github.io/REAlity/ and choose a file or complete folder. The browser worker inventories PE/.NET, ZIP, Electron ASAR, source maps, MSI/OLE and other signatures. It can extract supported ZIP/ASAR entries, PE resources and embedded source-map text. It does not decompile native instructions, .NET IL, DEX, Python bytecode or MSI tables itself. Limits: 256 MiB combined input, 384 MiB expanded, 64 MiB per member, bounded recursion. Unsupported formats, malformed archives and missing sources appear in the report.

If a standalone HTML entry point is present, choose its recovered bundle, review files and download the project ZIP. Native Electron APIs, server dependencies, absolute paths and missing code can require reconstruction. The original analyzer is still available at inspector.html.

## GitHub publishing

Create a new public repository with a README and main branch. Use a short-lived fine-grained token scoped only to that new repository, with Contents and Workflows write, Actions and Pages read, and Metadata read; GitHub may require other settings or approval. The optional OAuth relay below offers device sign-in but its public_repo and workflow OAuth scopes are broader. GitHub authorization is always explicit; the Pages origin cannot read GitHub's login cookies.

The frontend reviews project files, writes blobs and one commit to main with a non-forced ref update, and refuses to overwrite an existing project. It generates a Pages workflow using only static files in site/. No recovered build scripts run in CI. Enable GitHub Actions as the Pages source, then run the workflow if needed. Verify the exact published commit through the GitHub API. Successful deployment is not functional equivalence. Keep originals and secrets out of the public repository, and revoke tokens when finished.

## Optional remote service (not deployed by this repository)

Deploy remote_service.py behind an HTTPS reverse proxy on a dedicated, isolated worker. Use a trusted administrator, strict network egress rules, disk and memory limits, request rate limiting and timeouts. Do not run on a shared privileged host. The provided Dockerfile is an unprivileged minimal static/AI service, **not** a complete sandbox or a native decompiler image.

```sh
docker build -f Dockerfile.remote -t reality-remote .
docker run --rm --cap-drop ALL --security-opt no-new-privileges --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=6g --memory=8g --cpus=2 --pids-limit=128 \
  --env-file /secure/path/reality.env -p 127.0.0.1:8080:8080 reality-remote
```

Configure REALITY_WEB_ORIGIN (for the default site, https://marcusdhaynes.github.io), REALITY_SERVICE_KEY (random 32+ characters), REALITY_MODEL_BASE_URL (trusted OpenAI-compatible /v1 base URL), REALITY_MODEL, and REALITY_MODEL_KEY. Keep the environment file outside GitHub. Terminate TLS in a reverse proxy; the container itself listens on HTTP port 8080. Set appropriate proxy body and timeout limits. Only the configured origin and authenticated requests are accepted. Origin alone is not authentication.

The service accepts POST /v1/reconstruct with an application/zip body and Bearer service key. It runs bounded static recovery, supplies selected evidence to the configured AI provider, returns a ZIP of reviewed-format static web files and a limitations report, and removes its temporary workspace. It does not execute the original or generated code. AI output is inferred and may be incomplete or incorrect. No model provider or cloud VM has been provisioned. No promise of native code parity is made.

For enhanced static analysis, provision official REA/Ghidra, ILSpy, JADX, and other compatible tools in a dedicated sandboxed worker and explicitly set REALITY_EXTERNAL_STATIC=1. The default image contains none of those external tools. Do not enable this flag on a shared service without reviewing provider behavior, licensing, and isolation. Full runtime comparison, modern Windows virtualization, native WASM decompilation ports, automated multi-round builds and hosted compute remain future work.

### Optional GitHub device login

Register a GitHub OAuth application under Developer Settings, enable device flow and set REALITY_GITHUB_CLIENT_ID on your trusted relay. The browser uses the relay's HTTPS URL and service key, obtains a GitHub verification code, and opens GitHub's own authorization page. If already signed in, GitHub may reuse the session. The relay receives the OAuth token and passes it to the browser; use only a trusted relay. Tokens are kept in browser memory; disconnecting clears the local token but does not revoke the GitHub grant. Revoke the grant from GitHub when done. For least privilege prefer the single-repository fine-grained token.

### Verification

```sh
node --test tests/browser.test.mjs
python -m unittest -v
```

Pages deployment is gated by browser tests. Live user authorization, target-specific recovery, AI reconstruction and deployment need an end-to-end test with an authorized executable and actual hosting/credentials.
