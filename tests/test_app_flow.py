"""
End-to-End integration test of the Streamlit application using Streamlit AppTest.
Verifies all pages, buttons, and state changes execute without exceptions.
"""

import pytest
from streamlit.testing.v1 import AppTest


def test_app_loads_overview_page():
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    assert not at.exception
    # Check that title or breadcrumbs render
    assert len(at.markdown) > 0


def test_navigate_to_finance_simulator():
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    assert not at.exception

    # Switch radio to Finance Simulator
    at.sidebar.radio[0].set_value("Finance Simulator").run()
    assert not at.exception
    # Verify inputs are present
    assert len(at.number_input) >= 4


def test_navigate_to_scenario_comparison():
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    assert not at.exception

    at.sidebar.radio[0].set_value("Scenario Comparison").run()
    assert not at.exception


def test_navigate_to_sensitivity_analysis():
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    assert not at.exception

    at.sidebar.radio[0].set_value("Data Science & Sensitivity").run()
    assert not at.exception


def test_navigate_to_methodology_and_about():
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    assert not at.exception

    at.sidebar.radio[0].set_value("Insights & Methodology").run()
    assert not at.exception

    at.sidebar.radio[0].set_value("About the Project").run()
    assert not at.exception
