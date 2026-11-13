"""Compile both LaTeX documents with Tectonic or XeLaTeX, without console pop-ups."""
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent


def run():
    configured = os.environ.get("TECTONIC")
    executable = configured or shutil.which("tectonic") or shutil.which("xelatex")
    if not executable:
        raise RuntimeError("Install Tectonic or XeLaTeX, or set TECTONIC to its executable path.")
    folder = ROOT / "report"
    logs = folder / "build_logs"
    logs.mkdir(exist_ok=True)
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    tectonic = "tectonic" in Path(executable).name.lower()
    for stem in ("Tier1_Report", "report-template"):
        command = [executable, "--keep-logs", f"{stem}.tex"] if tectonic else [
            executable, "-interaction=nonstopmode", "-halt-on-error", f"{stem}.tex"]
        outputs = []
        for _ in range(1 if tectonic else 2):
            result = subprocess.run(command, cwd=folder, capture_output=True,
                                    encoding="utf-8", errors="replace", creationflags=flags)
            outputs.append(result.stdout + result.stderr)
            if result.returncode:
                (logs / f"{stem}.txt").write_text("\n".join(outputs), encoding="utf-8")
                raise RuntimeError(f"LaTeX compilation failed; see report/build_logs/{stem}.txt")
        (logs / f"{stem}.txt").write_text("\n".join(outputs), encoding="utf-8")
        print(f"Compiled report/{stem}.pdf", flush=True)


if __name__ == "__main__":
    run()
