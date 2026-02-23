"""
Generador de reportes para equipo TICS
Formatea resultados de analisis para facilitar correcciones
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TICSReporter:
    """Genera reportes estructurados para equipo TICS."""

    def __init__(self, output_dir: str = "../../output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generar_listado_correcciones_tabla(self, errores: List[Dict],
                                            nombre_tabla: str) -> str:
        """
        Genera listado de correcciones SQL sugeridas.

        Returns:
            Ruta al archivo generado
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ruta = self.output_dir / f"correcciones_tabla/{nombre_tabla}_correcciones_{timestamp}.sql"
        ruta.parent.mkdir(parents=True, exist_ok=True)

        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(f"-- Correcciones sugeridas para tabla: {nombre_tabla}\n")
            f.write(f"-- Generado: {datetime.now().isoformat()}\n")
            f.write(f"-- Total errores: {len(errores)}\n")
            f.write("-- IMPORTANTE: Revisar antes de ejecutar\n\n")

            # Agrupar por tipo de correccion
            correcciones_trim = []
            correcciones_null = []
            correcciones_formato = []
            otras = []

            for error in errores:
                tipo = error.get('tipo_error', '')
                if tipo == 'ESPACIOS_EXTRA':
                    correcciones_trim.append(error)
                elif tipo == 'CAMPO_VACIO':
                    correcciones_null.append(error)
                elif tipo in ('FORMATO_FECHA', 'CARACTERES_INVALIDOS'):
                    correcciones_formato.append(error)
                else:
                    otras.append(error)

            # Generar TRIM updates
            if correcciones_trim:
                campos_trim = set(e['campo'] for e in correcciones_trim)
                f.write("-- === CORRECCIONES DE ESPACIOS (TRIM) ===\n")
                for campo in campos_trim:
                    f.write(f"UPDATE {nombre_tabla} SET {campo} = TRIM({campo}) ")
                    f.write(f"WHERE {campo} != TRIM({campo});\n")
                f.write("\n")

            # Generar reporte de NULLs
            if correcciones_null:
                f.write("-- === CAMPOS VACIOS A REVISAR ===\n")
                f.write("-- Los siguientes registros tienen campos obligatorios vacios:\n")
                for error in correcciones_null[:20]:  # Limitar muestra
                    f.write(f"-- Fila {error['fila']}: {error['campo']} esta vacio\n")
                if len(correcciones_null) > 20:
                    f.write(f"-- ... y {len(correcciones_null) - 20} mas\n")
                f.write("\n")

            # Correcciones de formato
            if correcciones_formato:
                f.write("-- === CORRECCIONES DE FORMATO ===\n")
                f.write("-- Revisar estos registros manualmente:\n")
                for error in correcciones_formato[:20]:
                    f.write(f"-- Fila {error['fila']}, Campo {error['campo']}: ")
                    f.write(f"{error.get('mensaje', 'Error de formato')}\n")
                f.write("\n")

        logger.info(f"Archivo SQL generado: {ruta}")
        return str(ruta)

    def generar_listado_para_revision(self, errores: List[Dict],
                                       nombre_archivo: str) -> str:
        """
        Genera CSV con listado de registros para revision manual.

        Returns:
            Ruta al archivo generado
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ruta = self.output_dir / f"listados_tics/{nombre_archivo}_revision_{timestamp}.csv"
        ruta.parent.mkdir(parents=True, exist_ok=True)

        with open(ruta, 'w', newline='', encoding='utf-8') as f:
            campos = ['fila', 'campo', 'valor_actual', 'tipo_error',
                     'mensaje', 'accion_sugerida', 'prioridad']
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()

            for error in errores:
                error['prioridad'] = self._calcular_prioridad(error)
                writer.writerow({k: error.get(k, '') for k in campos})

        logger.info(f"Listado revision generado: {ruta}")
        return str(ruta)

    def generar_reporte_codigo(self, errores: List[Dict],
                                nombre_sistema: str) -> str:
        """
        Genera reporte de correcciones necesarias en codigo/configuracion.

        Returns:
            Ruta al archivo generado
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ruta = self.output_dir / f"correcciones_codigo/{nombre_sistema}_codigo_{timestamp}.md"
        ruta.parent.mkdir(parents=True, exist_ok=True)

        # Analizar patrones de errores
        errores_por_campo = {}
        for error in errores:
            campo = error.get('campo', 'DESCONOCIDO')
            if campo not in errores_por_campo:
                errores_por_campo[campo] = []
            errores_por_campo[campo].append(error)

        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(f"# Reporte de Correcciones - {nombre_sistema}\n\n")
            f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**Total errores:** {len(errores)}\n\n")

            f.write("## Resumen por Campo\n\n")
            f.write("| Campo | Cantidad Errores | Tipo Principal |\n")
            f.write("|-------|-----------------|----------------|\n")

            for campo, errs in sorted(errores_por_campo.items(),
                                      key=lambda x: -len(x[1])):
                tipos = {}
                for e in errs:
                    t = e.get('tipo_error', 'OTRO')
                    tipos[t] = tipos.get(t, 0) + 1
                tipo_principal = max(tipos.keys(), key=lambda x: tipos[x])
                f.write(f"| {campo} | {len(errs)} | {tipo_principal} |\n")

            f.write("\n## Sugerencias de Correccion en Codigo\n\n")

            # Sugerencias basadas en tipos de error
            sugerencias = self._generar_sugerencias_codigo(errores_por_campo)
            for sugerencia in sugerencias:
                f.write(f"### {sugerencia['titulo']}\n\n")
                f.write(f"{sugerencia['descripcion']}\n\n")
                if sugerencia.get('codigo'):
                    f.write("```python\n")
                    f.write(sugerencia['codigo'])
                    f.write("\n```\n\n")

        logger.info(f"Reporte codigo generado: {ruta}")
        return str(ruta)

    def generar_resumen_ejecutivo(self, estadisticas: Dict,
                                   nombre_proyecto: str) -> str:
        """
        Genera resumen ejecutivo para supervision.

        Returns:
            Ruta al archivo generado
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ruta = self.output_dir / f"listados_tics/{nombre_proyecto}_resumen_{timestamp}.txt"
        ruta.parent.mkdir(parents=True, exist_ok=True)

        with open(ruta, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(f"RESUMEN EJECUTIVO - ANALISIS DE DATOS RCE\n")
            f.write(f"Proyecto: {nombre_proyecto}\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("=" * 70 + "\n\n")

            f.write("METRICAS GENERALES:\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Total registros analizados: {estadisticas.get('total_filas', 0):,}\n")
            f.write(f"  Registros con errores:      {estadisticas.get('filas_con_error', 0):,}\n")

            total = estadisticas.get('total_filas', 1)
            con_error = estadisticas.get('filas_con_error', 0)
            tasa = (con_error / total * 100) if total > 0 else 0
            f.write(f"  Tasa de error:              {tasa:.2f}%\n\n")

            f.write("DISTRIBUCION DE ERRORES POR TIPO:\n")
            f.write("-" * 40 + "\n")
            for tipo, cantidad in sorted(
                estadisticas.get('errores_por_tipo', {}).items(),
                key=lambda x: -x[1]
            ):
                f.write(f"  {tipo:25s}: {cantidad:6,}\n")

            f.write("\n")
            f.write("CAMPOS MAS AFECTADOS:\n")
            f.write("-" * 40 + "\n")
            for campo, cantidad in sorted(
                estadisticas.get('errores_por_campo', {}).items(),
                key=lambda x: -x[1]
            )[:10]:
                f.write(f"  {campo:25s}: {cantidad:6,}\n")

            f.write("\n" + "=" * 70 + "\n")
            f.write("ACCIONES RECOMENDADAS:\n")
            f.write("-" * 40 + "\n")
            f.write("1. Revisar listados CSV adjuntos para detalle de errores\n")
            f.write("2. Ejecutar scripts SQL de correccion (previa revision)\n")
            f.write("3. Coordinar con desarrollo para correcciones de codigo\n")
            f.write("=" * 70 + "\n")

        logger.info(f"Resumen ejecutivo generado: {ruta}")
        return str(ruta)

    def _calcular_prioridad(self, error: Dict) -> str:
        """Calcula prioridad de correccion."""
        tipo = error.get('tipo_error', '')

        prioridades = {
            'CAMPO_VACIO': 'ALTA',
            'VALOR_INVALIDO': 'ALTA',
            'FORMATO_FECHA': 'MEDIA',
            'LONGITUD_EXCEDIDA': 'MEDIA',
            'ESPACIOS_EXTRA': 'BAJA',
            'CARACTERES_INVALIDOS': 'MEDIA'
        }

        return prioridades.get(tipo, 'MEDIA')

    def _generar_sugerencias_codigo(self, errores_por_campo: Dict) -> List[Dict]:
        """Genera sugerencias de codigo basadas en errores encontrados."""
        sugerencias = []

        # Analizar si hay muchos errores de espacios
        total_espacios = sum(
            len([e for e in errs if e.get('tipo_error') == 'ESPACIOS_EXTRA'])
            for errs in errores_por_campo.values()
        )

        if total_espacios > 10:
            sugerencias.append({
                'titulo': 'Sanitizacion de entrada',
                'descripcion': 'Se detectaron muchos campos con espacios extra. '
                              'Agregar sanitizacion en el punto de entrada.',
                'codigo': '''def sanitizar_campo(valor):
    """Limpia espacios y caracteres de control."""
    if valor is None:
        return valor
    return str(valor).strip()'''
            })

        # Analizar fechas
        total_fechas = sum(
            len([e for e in errs if e.get('tipo_error') == 'FORMATO_FECHA'])
            for errs in errores_por_campo.values()
        )

        if total_fechas > 5:
            sugerencias.append({
                'titulo': 'Normalizacion de fechas',
                'descripcion': 'Se detectaron multiples formatos de fecha. '
                              'Implementar conversion a formato estandar.',
                'codigo': '''from datetime import datetime

def normalizar_fecha(valor, formatos=None):
    """Convierte fecha a formato ISO."""
    formatos = formatos or ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']
    for fmt in formatos:
        try:
            return datetime.strptime(valor, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None'''
            })

        return sugerencias
