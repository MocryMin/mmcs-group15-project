"""Run the full build in order."""
import pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
for script in ["src/prepare_data.py", "src/run_cases.py", "src/verify.py", "src/make_figures.py"]:
    print("==", script)
    r = subprocess.run([sys.executable, "-X", "utf8", str(HERE / script)], cwd=str(HERE))
    if r.returncode:
        raise SystemExit(f"{script} failed with {r.returncode}")
print("done")
