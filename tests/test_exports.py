"""
Unit tests for PDF export (ReportLab) and CSV schedule export.
"""

import io
from src.calculations import SimulationInputs, calculate_simulation
from src.scenarios import get_default_preset_scenarios
from src.report_generator import generate_pdf_report, generate_csv_export


def test_pdf_report_generation():
    inputs = SimulationInputs(
        monthly_income=40000.0,
        essential_expenses=18000.0,
        discretionary_expenses=8000.0,
        current_savings=50000.0,
        monthly_contribution=8000.0,
        duration_years=5,
        annual_inflation=5.0,
        annual_return=7.0,
    )
    outputs = calculate_simulation(inputs)
    presets = get_default_preset_scenarios(inputs)

    pdf_buffer = generate_pdf_report(
        scenario_name="Test Executive Scenario",
        inputs=inputs,
        outputs=outputs,
        comparison_scenarios=presets,
    )

    assert isinstance(pdf_buffer, io.BytesIO)
    pdf_bytes = pdf_buffer.getvalue()
    assert len(pdf_bytes) > 1000
    # PDF magic bytes "%PDF-"
    assert pdf_bytes.startswith(b"%PDF-")


def test_csv_export_generation():
    inputs = SimulationInputs(
        monthly_income=40000.0,
        essential_expenses=18000.0,
        discretionary_expenses=8000.0,
        current_savings=50000.0,
        monthly_contribution=8000.0,
        duration_years=3,
    )
    csv_str = generate_csv_export(inputs)
    assert isinstance(csv_str, str)
    assert "Year" in csv_str
    assert "Ending_Balance" in csv_str
    lines = csv_str.strip().split("\n")
    # Header + 3 years = 4 lines
    assert len(lines) == 4
