"""
Validadores de campos especificos para datos RCE
"""

import re
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any


class FieldValidator:
    """Validador de campos con reglas especificas RCE."""

    # Patrones comunes
    PATRON_RUT = r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$'
    PATRON_EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PATRON_TELEFONO = r'^\+?56?\d{9}$'
    PATRON_CODIGO_ALFA = r'^[A-Z0-9]+$'

    def __init__(self, reglas_custom: Dict = None):
        self.reglas_custom = reglas_custom or {}
        self.errores_acumulados = []

    def validar_rut(self, valor: str) -> Tuple[bool, str]:
        """
        Valida formato y digito verificador de RUT chileno.

        Returns:
            Tuple (es_valido, mensaje)
        """
        if not valor:
            return False, "RUT vacio"

        # Limpiar formato
        rut_limpio = valor.replace(".", "").replace("-", "").upper()

        if len(rut_limpio) < 2:
            return False, "RUT muy corto"

        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]

        # Validar que cuerpo sea numerico
        if not cuerpo.isdigit():
            return False, "Cuerpo del RUT debe ser numerico"

        # Calcular digito verificador
        suma = 0
        multiplo = 2
        for c in reversed(cuerpo):
            suma += int(c) * multiplo
            multiplo = multiplo + 1 if multiplo < 7 else 2

        resto = suma % 11
        dv_calculado = 11 - resto

        if dv_calculado == 11:
            dv_esperado = '0'
        elif dv_calculado == 10:
            dv_esperado = 'K'
        else:
            dv_esperado = str(dv_calculado)

        if dv != dv_esperado:
            return False, f"Digito verificador invalido (esperado: {dv_esperado})"

        return True, "RUT valido"

    def validar_fecha(self, valor: str, formatos: List[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Valida y normaliza fecha.

        Returns:
            Tuple (es_valido, mensaje, fecha_normalizada)
        """
        if not valor:
            return False, "Fecha vacia", None

        formatos = formatos or [
            '%Y-%m-%d',      # 2024-01-15
            '%d/%m/%Y',      # 15/01/2024
            '%d-%m-%Y',      # 15-01-2024
            '%Y/%m/%d',      # 2024/01/15
            '%d.%m.%Y',      # 15.01.2024
        ]

        for fmt in formatos:
            try:
                fecha = datetime.strptime(valor.strip(), fmt)
                # Validar rango razonable
                if fecha.year < 1900 or fecha.year > 2100:
                    return False, f"Ano fuera de rango: {fecha.year}", None
                return True, "Fecha valida", fecha.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return False, f"Formato de fecha no reconocido: {valor}", None

    def validar_email(self, valor: str) -> Tuple[bool, str]:
        """Valida formato de email."""
        if not valor:
            return False, "Email vacio"

        if re.match(self.PATRON_EMAIL, valor.strip()):
            return True, "Email valido"
        return False, "Formato de email invalido"

    def validar_telefono(self, valor: str) -> Tuple[bool, str]:
        """Valida formato de telefono chileno."""
        if not valor:
            return False, "Telefono vacio"

        # Limpiar
        tel_limpio = re.sub(r'[\s\-\(\)]', '', valor)

        if re.match(self.PATRON_TELEFONO, tel_limpio):
            return True, "Telefono valido"
        return False, "Formato de telefono invalido"

    def validar_codigo(self, valor: str, longitud_min: int = 1,
                       longitud_max: int = 50) -> Tuple[bool, str]:
        """Valida codigo alfanumerico."""
        if not valor:
            return False, "Codigo vacio"

        valor = valor.strip()

        if len(valor) < longitud_min:
            return False, f"Codigo muy corto (min: {longitud_min})"

        if len(valor) > longitud_max:
            return False, f"Codigo muy largo (max: {longitud_max})"

        if not re.match(self.PATRON_CODIGO_ALFA, valor):
            return False, "Codigo debe ser alfanumerico mayusculas"

        return True, "Codigo valido"

    def validar_enum(self, valor: str, valores_validos: List[str],
                     case_sensitive: bool = False) -> Tuple[bool, str]:
        """Valida que valor este en lista de valores permitidos."""
        if not valor:
            return False, "Valor vacio"

        valor_comparar = valor if case_sensitive else valor.upper()
        valores_comparar = valores_validos if case_sensitive else [v.upper() for v in valores_validos]

        if valor_comparar in valores_comparar:
            return True, "Valor valido"

        return False, f"Valor '{valor}' no esta en lista permitida: {valores_validos}"

    def validar_numerico(self, valor: str, min_val: float = None,
                         max_val: float = None) -> Tuple[bool, str]:
        """Valida campo numerico con rango opcional."""
        if not valor:
            return False, "Valor vacio"

        try:
            numero = float(valor.replace(',', '.'))
        except ValueError:
            return False, f"'{valor}' no es numerico"

        if min_val is not None and numero < min_val:
            return False, f"Valor {numero} menor al minimo {min_val}"

        if max_val is not None and numero > max_val:
            return False, f"Valor {numero} mayor al maximo {max_val}"

        return True, "Valor numerico valido"

    def detectar_tipo_campo(self, valores: List[str]) -> str:
        """
        Intenta detectar el tipo de campo basado en muestreo de valores.

        Returns:
            Tipo detectado: 'fecha', 'numerico', 'rut', 'email', 'texto'
        """
        if not valores:
            return 'texto'

        # Filtrar vacios
        valores_no_vacios = [v for v in valores if v and str(v).strip()]

        if not valores_no_vacios:
            return 'texto'

        muestra = valores_no_vacios[:100]  # Analizar primeros 100

        # Contar matches por tipo
        tipos_match = {
            'fecha': 0,
            'numerico': 0,
            'rut': 0,
            'email': 0
        }

        for valor in muestra:
            valor = str(valor).strip()

            if self.validar_fecha(valor)[0]:
                tipos_match['fecha'] += 1
            if self.validar_numerico(valor)[0]:
                tipos_match['numerico'] += 1
            if self.validar_rut(valor)[0]:
                tipos_match['rut'] += 1
            if self.validar_email(valor)[0]:
                tipos_match['email'] += 1

        # Determinar tipo predominante (>80% match)
        umbral = len(muestra) * 0.8
        for tipo, cantidad in tipos_match.items():
            if cantidad >= umbral:
                return tipo

        return 'texto'

    def generar_reporte_validacion(self, datos: List[Dict],
                                   reglas: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Ejecuta validacion completa y genera reporte.

        Args:
            datos: Lista de diccionarios con datos a validar
            reglas: Diccionario campo -> {tipo, obligatorio, ...}

        Returns:
            Reporte de validacion
        """
        errores = []
        estadisticas = {'total': len(datos), 'errores': 0}

        for idx, fila in enumerate(datos):
            for campo, config in reglas.items():
                valor = fila.get(campo, '')
                tipo = config.get('tipo', 'texto')
                obligatorio = config.get('obligatorio', False)

                # Validar obligatoriedad
                if obligatorio and not valor:
                    errores.append({
                        'fila': idx + 1,
                        'campo': campo,
                        'error': 'Campo obligatorio vacio',
                        'valor': valor
                    })
                    continue

                if not valor:
                    continue

                # Validar segun tipo
                es_valido, mensaje = True, ""

                if tipo == 'rut':
                    es_valido, mensaje = self.validar_rut(valor)
                elif tipo == 'fecha':
                    es_valido, mensaje, _ = self.validar_fecha(valor)
                elif tipo == 'email':
                    es_valido, mensaje = self.validar_email(valor)
                elif tipo == 'numerico':
                    es_valido, mensaje = self.validar_numerico(
                        valor,
                        config.get('min'),
                        config.get('max')
                    )
                elif tipo == 'enum':
                    es_valido, mensaje = self.validar_enum(
                        valor,
                        config.get('valores_validos', [])
                    )

                if not es_valido:
                    errores.append({
                        'fila': idx + 1,
                        'campo': campo,
                        'error': mensaje,
                        'valor': valor
                    })

        estadisticas['errores'] = len(errores)

        return {
            'estadisticas': estadisticas,
            'errores': errores
        }
