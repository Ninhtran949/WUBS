"""Install a built wheel in a fresh environment outside the source checkout."""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--uv", type=Path, required=True)
    args = parser.parse_args()
    wheel = args.wheel.resolve(strict=True)
    uv = args.uv.resolve(strict=True)
    assert wheel.suffix == ".whl", "Expected a built wheel"
    with tempfile.TemporaryDirectory(prefix="stresslab-wheel-") as directory:
        root = Path(directory)
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment.pop("VIRTUAL_ENV", None)
        venv = root / "venv"
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        console = venv / (
            "Scripts/stresslab.exe" if os.name == "nt" else "bin/stresslab"
        )
        # shortcut: dependency-free T01 wheel; provision locked runtime deps in T02.
        for command in (
            [str(uv), "venv", str(venv), "--python", sys.executable, "--offline"],
            [
                str(uv),
                "pip",
                "install",
                "--python",
                str(python),
                "--offline",
                "--no-deps",
                str(wheel),
            ],
        ):
            subprocess.run(command, cwd=root, env=environment, check=True, timeout=60)
        for flag in ("--help", "--version"):
            result = subprocess.run(
                [str(console), flag],
                cwd=root,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert "stresslab" in result.stdout, result.stdout
        check = subprocess.run(
            [
                str(python),
                "-I",
                "-c",
                "from pathlib import Path; import web_stress_lab; "
                "assert 'site-packages' in Path(web_stress_lab.__file__).parts; "
                "from importlib.metadata import version; "
                "print(version('web-stress-lab'))",
            ],
            cwd=root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        print(
            f"PASS: installed wheel {check.stdout.strip()}, CLI help/version, isolated import"
        )


if __name__ == "__main__":
    main()
