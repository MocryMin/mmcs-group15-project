"""Run this in an experiment copy to preserve original outputs."""
from pathlib import Path
import run_grid

if __name__=="__main__":
    run_grid.PREVIOUS=Path(__file__).resolve().parent/"reference_previous"
    run_grid.main()
    import analyse_grid
    analyse_grid.main()
