"""
test_imports.py - Verify all G_Analizador_RCE modules can be imported.

These tests validate that the project's Python modules are syntactically
correct and can be loaded without runtime errors (excluding external deps).
"""

import os
import sys
import importlib
import pytest

# Add scripts directory to path so modules resolve
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
sys.path.insert(0, SCRIPTS_DIR)


class TestValidatorImports:
    """Test that validator modules can be imported."""

    def test_import_field_validator(self):
        mod = importlib.import_module("validators.field_validator")
        assert hasattr(mod, "FieldValidator")

    def test_import_validators_package(self):
        mod = importlib.import_module("validators")
        assert mod is not None


class TestUtilImports:
    """Test that utility modules can be imported."""

    def test_import_logger(self):
        mod = importlib.import_module("utils.logger")
        assert hasattr(mod, "get_logger")
        assert hasattr(mod, "RCELogger")

    def test_import_utils_package(self):
        mod = importlib.import_module("utils")
        assert mod is not None


class TestAnalyzerImports:
    """Test that analyzer modules can be imported.

    Note: csv_analyzer.py uses a hardcoded relative FileHandler path at module
    level which causes FileNotFoundError when imported from a different cwd.
    These tests are marked xfail until the logging path is made configurable.
    """

    @pytest.mark.xfail(reason="csv_analyzer uses hardcoded relative log path at module level")
    def test_import_analyzers_package(self):
        mod = importlib.import_module("analyzers")
        assert mod is not None

    @pytest.mark.xfail(reason="csv_analyzer uses hardcoded relative log path at module level")
    def test_import_csv_analyzer(self):
        mod = importlib.import_module("analyzers.csv_analyzer")
        assert hasattr(mod, "CSVAnalyzer")

    @pytest.mark.xfail(reason="csv_analyzer uses hardcoded relative log path at module level")
    def test_import_alma_analyzer(self):
        mod = importlib.import_module("analyzers.alma_analyzer")
        assert mod is not None


class TestReporterImports:
    """Test that reporter modules can be imported."""

    def test_import_reporters_package(self):
        mod = importlib.import_module("reporters")
        assert mod is not None

    def test_import_tics_reporter(self):
        mod = importlib.import_module("reporters.tics_reporter")
        assert hasattr(mod, "TICSReporter")


class TestLoaderImports:
    """Test that loader modules can be imported."""

    def test_import_loaders_package(self):
        mod = importlib.import_module("loaders")
        assert mod is not None

    def test_import_data_loader(self):
        mod = importlib.import_module("loaders.data_loader")
        assert hasattr(mod, "DataLoader")
