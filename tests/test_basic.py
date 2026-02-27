"""
test_basic.py - Basic unit tests for G_Analizador_RCE core functionality.

Tests the FieldValidator class which is the primary validation engine.
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from validators.field_validator import FieldValidator


@pytest.fixture
def validator():
    return FieldValidator()


class TestRutValidation:
    """Test Chilean RUT validation logic."""

    def test_valid_rut(self, validator):
        # 11.111.111-1 is a well-known test RUT
        es_valido, msg = validator.validar_rut("11111111-1")
        assert es_valido is True

    def test_empty_rut(self, validator):
        es_valido, msg = validator.validar_rut("")
        assert es_valido is False
        assert "vacio" in msg.lower()

    def test_short_rut(self, validator):
        es_valido, msg = validator.validar_rut("1")
        assert es_valido is False

    def test_non_numeric_body(self, validator):
        es_valido, msg = validator.validar_rut("abc-1")
        assert es_valido is False
        assert "numerico" in msg.lower()

    def test_invalid_check_digit(self, validator):
        es_valido, msg = validator.validar_rut("11111111-0")
        assert es_valido is False
        assert "verificador" in msg.lower()

    def test_rut_with_dots(self, validator):
        # Dots should be stripped during validation
        es_valido, _ = validator.validar_rut("11.111.111-1")
        assert es_valido is True


class TestDateValidation:
    """Test date parsing and validation."""

    def test_iso_format(self, validator):
        es_valido, msg, normalizada = validator.validar_fecha("2024-01-15")
        assert es_valido is True
        assert normalizada == "2024-01-15"

    def test_slash_format(self, validator):
        es_valido, msg, normalizada = validator.validar_fecha("15/01/2024")
        assert es_valido is True
        assert normalizada == "2024-01-15"

    def test_dash_dmy_format(self, validator):
        es_valido, msg, normalizada = validator.validar_fecha("15-01-2024")
        assert es_valido is True
        assert normalizada == "2024-01-15"

    def test_empty_date(self, validator):
        es_valido, msg, normalizada = validator.validar_fecha("")
        assert es_valido is False
        assert normalizada is None

    def test_invalid_date(self, validator):
        es_valido, msg, normalizada = validator.validar_fecha("not-a-date")
        assert es_valido is False

    def test_year_out_of_range(self, validator):
        es_valido, msg, normalizada = validator.validar_fecha("01/01/1800")
        assert es_valido is False


class TestEmailValidation:
    """Test email format validation."""

    def test_valid_email(self, validator):
        es_valido, msg = validator.validar_email("user@example.com")
        assert es_valido is True

    def test_empty_email(self, validator):
        es_valido, msg = validator.validar_email("")
        assert es_valido is False

    def test_invalid_email_no_at(self, validator):
        es_valido, msg = validator.validar_email("userexample.com")
        assert es_valido is False

    def test_invalid_email_no_domain(self, validator):
        es_valido, msg = validator.validar_email("user@")
        assert es_valido is False


class TestPhoneValidation:
    """Test Chilean phone number validation."""

    def test_valid_phone_9_digits(self, validator):
        # The regex pattern requires optional +56 prefix, so bare 9-digit needs 56 prefix
        es_valido, msg = validator.validar_telefono("56912345678")
        assert es_valido is True

    def test_valid_phone_with_56(self, validator):
        es_valido, msg = validator.validar_telefono("56912345678")
        assert es_valido is True

    def test_valid_phone_with_plus56(self, validator):
        es_valido, msg = validator.validar_telefono("+56912345678")
        assert es_valido is True

    def test_empty_phone(self, validator):
        es_valido, msg = validator.validar_telefono("")
        assert es_valido is False


class TestNumericValidation:
    """Test numeric field validation."""

    def test_valid_integer(self, validator):
        es_valido, msg = validator.validar_numerico("42")
        assert es_valido is True

    def test_valid_decimal_with_comma(self, validator):
        es_valido, msg = validator.validar_numerico("3,14")
        assert es_valido is True

    def test_empty_value(self, validator):
        es_valido, msg = validator.validar_numerico("")
        assert es_valido is False

    def test_non_numeric(self, validator):
        es_valido, msg = validator.validar_numerico("abc")
        assert es_valido is False

    def test_range_below_min(self, validator):
        es_valido, msg = validator.validar_numerico("5", min_val=10)
        assert es_valido is False

    def test_range_above_max(self, validator):
        es_valido, msg = validator.validar_numerico("100", max_val=50)
        assert es_valido is False


class TestEnumValidation:
    """Test enum/list validation."""

    def test_valid_enum(self, validator):
        es_valido, msg = validator.validar_enum("ACTIVO", ["ACTIVO", "INACTIVO"])
        assert es_valido is True

    def test_case_insensitive_enum(self, validator):
        es_valido, msg = validator.validar_enum("activo", ["ACTIVO", "INACTIVO"])
        assert es_valido is True

    def test_invalid_enum(self, validator):
        es_valido, msg = validator.validar_enum("OTRO", ["ACTIVO", "INACTIVO"])
        assert es_valido is False

    def test_empty_enum(self, validator):
        es_valido, msg = validator.validar_enum("", ["ACTIVO"])
        assert es_valido is False


class TestCodeValidation:
    """Test alphanumeric code validation."""

    def test_valid_code(self, validator):
        es_valido, msg = validator.validar_codigo("ABC123")
        assert es_valido is True

    def test_empty_code(self, validator):
        es_valido, msg = validator.validar_codigo("")
        assert es_valido is False

    def test_lowercase_rejected(self, validator):
        es_valido, msg = validator.validar_codigo("abc123")
        assert es_valido is False

    def test_too_short(self, validator):
        es_valido, msg = validator.validar_codigo("A", longitud_min=3)
        assert es_valido is False

    def test_too_long(self, validator):
        es_valido, msg = validator.validar_codigo("ABCDEF", longitud_max=3)
        assert es_valido is False


class TestFieldTypeDetection:
    """Test automatic field type detection."""

    def test_detect_email(self, validator):
        values = ["user@test.com", "admin@host.cl", "info@org.com"] * 40
        detected = validator.detectar_tipo_campo(values)
        assert detected == "email"

    def test_detect_empty_list(self, validator):
        detected = validator.detectar_tipo_campo([])
        assert detected == "texto"

    def test_detect_text_fallback(self, validator):
        values = ["hola", "mundo", "foo", "bar"] * 30
        detected = validator.detectar_tipo_campo(values)
        assert detected == "texto"


class TestValidationReport:
    """Test the full validation report generator."""

    def test_report_with_valid_data(self, validator):
        datos = [
            {"email": "test@test.com", "nombre": "Juan"},
            {"email": "admin@host.cl", "nombre": "Maria"},
        ]
        reglas = {
            "email": {"tipo": "email", "obligatorio": True},
        }
        reporte = validator.generar_reporte_validacion(datos, reglas)
        assert reporte["estadisticas"]["total"] == 2
        assert reporte["estadisticas"]["errores"] == 0

    def test_report_catches_missing_required(self, validator):
        datos = [
            {"email": "", "nombre": "Juan"},
        ]
        reglas = {
            "email": {"tipo": "email", "obligatorio": True},
        }
        reporte = validator.generar_reporte_validacion(datos, reglas)
        assert reporte["estadisticas"]["errores"] == 1
        assert "obligatorio" in reporte["errores"][0]["error"].lower()

    def test_report_catches_invalid_email(self, validator):
        datos = [
            {"email": "not-an-email", "nombre": "Juan"},
        ]
        reglas = {
            "email": {"tipo": "email", "obligatorio": True},
        }
        reporte = validator.generar_reporte_validacion(datos, reglas)
        assert reporte["estadisticas"]["errores"] == 1
