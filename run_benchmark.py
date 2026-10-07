from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run_cmd(args: list[str]) -> None:
    print("\n$ " + " ".join(map(str, args)))
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)

def main() -> None:
    if not (ROOT / "data" / "dataset.csv").exists():
        raise FileNotFoundError(
            "data/dataset.csv was not found. Put your original repository dataset there."
        )
    run_cmd([sys.executable, "scripts/validate_artifact.py"])
    run_cmd([sys.executable, "src/finalize.py"])
    figure_script = ROOT / "results" / "figures" / "generate_figures.py"
    if figure_script.exists():
        run_cmd([sys.executable, str(figure_script.relative_to(ROOT))])
    run_cmd([sys.executable, "scripts/validate_artifact.py"])
    print("\nDONE — benchmark results are in results/.")

if __name__ == "__main__":
    main()
