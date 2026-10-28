#!/usr/bin/env python3
"""Check that a Qwen3TTS-only consumer can resolve an explicit MLX version."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mlx-version", default="0.33.0")
    parser.add_argument("--scratch-path", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="speech-mlx-consumer-") as folder:
        consumer = Path(folder)
        (consumer / "Sources/Probe").mkdir(parents=True)
        (consumer / "Sources/Probe/main.swift").write_text("import Qwen3TTS\n")
        manifest = '''// swift-tools-version: 6.2
import PackageDescription
let package = Package(name: "Consumer", platforms: [.macOS(.v15)], dependencies: [
    .package(name: "speech-swift", path: SPEECH_PATH),
    .package(url: "https://github.com/ml-explore/mlx-swift", exact: MLX_VERSION)
], targets: [.executableTarget(name: "Probe", dependencies: [
    .product(name: "Qwen3TTS", package: "speech-swift"),
    .product(name: "MLX", package: "mlx-swift")
])])
'''
        manifest = manifest.replace("SPEECH_PATH", json.dumps(str(root)))
        manifest = manifest.replace("MLX_VERSION", json.dumps(args.mlx_version))
        (consumer / "Package.swift").write_text(manifest)
        command = ["swift", "package", "--package-path", str(consumer)]
        if args.scratch_path:
            command += ["--scratch-path", str(args.scratch_path.resolve())]
        subprocess.run(command + ["resolve"], check=True)
        pins = json.loads((consumer / "Package.resolved").read_text())["pins"]
        selected = next((pin.get("state", {}).get("version") for pin in pins if pin["identity"] == "mlx-swift"), None)
        if selected != args.mlx_version:
            raise RuntimeError(f"Expected MLX {args.mlx_version}, resolved {selected}")
        print(f"Qwen3TTS consumer resolves MLX {selected}")


if __name__ == "__main__":
    main()
