"""Install a built wheel in a fresh environment outside the source checkout."""

import argparse
import hashlib
import json
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
        requirements = root / "runtime-requirements.txt"
        subprocess.run(
            [
                str(uv),
                "export",
                "--project",
                str(Path(__file__).resolve().parents[1]),
                "--locked",
                "--offline",
                "--all-extras",
                "--no-dev",
                "--no-emit-project",
                "--format",
                "requirements.txt",
                "--output-file",
                str(requirements),
                "--quiet",
            ],
            cwd=root,
            env=environment,
            check=True,
            timeout=60,
        )
        wheel_hash = hashlib.sha256(wheel.read_bytes()).hexdigest()
        with requirements.open("a", encoding="utf-8") as output:
            output.write(
                f"\nweb-stress-lab @ {wheel.as_uri()} --hash=sha256:{wheel_hash}\n"
            )
        for command in (
            [str(uv), "venv", str(venv), "--python", sys.executable, "--offline"],
            [
                str(uv),
                "pip",
                "install",
                "--python",
                str(python),
                "--offline",
                "--default-index",
                "https://pypi.org/simple",
                "--require-hashes",
                # Export includes transitive dependencies; check the installed graph below.
                "--no-deps",
                "--only-binary",
                ":all:",
                "--requirements",
                str(requirements),
            ],
        ):
            subprocess.run(command, cwd=root, env=environment, check=True, timeout=60)
        subprocess.run(
            [str(uv), "pip", "check", "--python", str(python), "--offline"],
            cwd=root,
            env=environment,
            check=True,
            timeout=30,
        )
        for flag in ("--help", "--version"):
            result = subprocess.run(
                [str(console), flag],
                cwd=root,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, result.stderr
            assert "stresslab" in result.stdout, result.stdout
        config = root / "experiment.json"
        config.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "engine": "browser",
                    "target": {"origin": "http://127.0.0.1:8765"},
                    "scope": {
                        "allowed_origins": ["http://127.0.0.1:8765"],
                        "allowed_scenarios": ["LOGIN"],
                    },
                    "scenarios": [{"id": "LOGIN"}],
                    "accounts": {"catalog": "accounts.synthetic.json"},
                }
            ),
            encoding="utf-8",
        )
        validation = subprocess.run(
            [str(console), "validate-config", str(config), "--json"],
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert validation.returncode == 0, validation.stderr
        validated = json.loads(validation.stdout)
        assert validated["ok"] is True and validated["execution_checked"] is False
        catalog = root / "accounts.synthetic.json"
        catalog.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "accounts": [
                        {
                            "account_id": "wheel-smoke",
                            "username": "synthetic-wheel-smoke",
                            "password_ref": "env:STRESSLAB_WHEEL_SMOKE_PASSWORD",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        environment["STRESSLAB_WHEEL_SMOKE_PASSWORD"] = "wheel-smoke-only"
        check = subprocess.run(
            [
                str(python),
                "-I",
                "-c",
                "import sys; from pathlib import Path; import web_stress_lab; "
                "assert 'site-packages' in Path(web_stress_lab.__file__).parts; "
                "from web_stress_lab.interfaces.accounts import load_accounts; "
                "from web_stress_lab.infrastructure.secrets "
                "import EnvironmentSecretProvider; "
                "accounts = load_accounts(Path(sys.argv[1]), "
                "include_ids=('wheel-smoke',)); assert len(accounts) == 1; "
                "assert EnvironmentSecretProvider().resolve(accounts[0].password_ref) "
                "== 'wheel-smoke-only'; "
                "from importlib.metadata import version; "
                "print(version('web-stress-lab'))",
                str(catalog),
            ],
            cwd=root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        print(
            f"PASS: installed wheel {check.stdout.strip()}, hashed locked runtime deps, "
            "CLI help/version/static validation, catalog/secret provider, isolated import"
        )


if __name__ == "__main__":
    main()
