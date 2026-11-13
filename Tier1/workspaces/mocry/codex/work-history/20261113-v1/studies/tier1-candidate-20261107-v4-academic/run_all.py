"""Recalculate the candidate package and regenerate its report figures and tables."""
import run_study
import extend_study
import build_report
import verify_results


if __name__ == "__main__":
    run_study.run()
    extend_study.run()
    build_report.run()
    verify_results.run()
    import sys
    if "--pdf" in sys.argv[1:]:
        import build_pdf
        build_pdf.run()
