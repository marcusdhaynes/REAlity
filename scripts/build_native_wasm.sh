#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
mkdir -p docs/vendor/native
rustup toolchain install 1.97.0 --profile minimal --target wasm32-unknown-unknown
export RUSTUP_TOOLCHAIN=1.97.0
cargo test --manifest-path native-wasm/Cargo.toml
cargo build --release --target wasm32-unknown-unknown --manifest-path native-wasm/Cargo.toml
version="$(cargo metadata --manifest-path native-wasm/Cargo.toml --format-version 1 --filter-platform wasm32-unknown-unknown | python3 -c 'import json,sys; p=json.load(sys.stdin)["packages"]; v={x["version"] for x in p if x["name"]=="wasm-bindgen"}; assert len(v)==1; print(v.pop())')"
cargo install wasm-bindgen-cli --version "$version" --locked
wasm-bindgen --target web --out-dir docs/vendor/native --out-name reality_native native-wasm/target/wasm32-unknown-unknown/release/reality_native_wasm.wasm
test -s docs/vendor/native/reality_native_bg.wasm
test -s docs/vendor/native/reality_native.js
cargo metadata --manifest-path native-wasm/Cargo.toml --format-version 1 --filter-platform wasm32-unknown-unknown | python3 -c 'import json,sys; p=json.load(sys.stdin)["packages"]; print("\n".join("{} {} | {} | {}".format(x["name"],x["version"],x.get("license") or "see upstream license",x.get("repository") or "") for x in p))' > docs/vendor/native/DEPENDENCIES.txt
printf '%s\n' 'Native decompiler engine: Craft Anything (MIT OR Apache-2.0)' 'https://github.com/storytold/craft-anything/tree/48a9c5a60ff83ff620f98661339be6281a7debc6' > docs/vendor/native/NOTICE.txt
