"""
Analizador principal de archivos CSV para datos RCE
Uso: python csv_analyzer.py <archivo.csv> [--config config.json]
"""

import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('../../logs/analisis/analisis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CSVAnalyzer:
    """Analizador de archivos CSV para identificar campos a corregir."""

    def __init__(self, config_path: str = None):
        self.config = self._cargar_config(config_path)
        self.errores = []
        self.estadisticas = {
            'total_filas': 0,
            'filas_con_error': 0,
            'errores_por_campo': {},
            'errores_por_tipo': {}
        }

    def _cargar_config(self, config_path: str) -> Dict:
        """Carga configuracion desde archivo JSON."""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def analizar_archivo(self, archivo_csv: str) -> Dict[str, Any]:
        """
        Analiza un archivo CSV y retorna errores encontrados.

        Args:
            archivo_csv: Ruta al archivo CSV a analizar

        Returns:
            Diccionario con resultados del analisis
        """
        logger.info(f"Iniciando analisis de: {archivo_csv}")

        try:
            with open(archivo_csv, 'r', encoding='utf-8') as f:
                # Detectar delimitador
                sample = f.read(4096)
                f.seek(0)

                sniffer = csv.Sniffer()
                try:
                    dialect = sniffer.sniff(sample)
                except csv.Error:
                    dialect = csv.excel

                reader = csv.DictReader(f, dialect=dialect)
                headers = reader.fieldnames

                logger.info(f"Columnas detectadas: {headers}")

                for num_fila, fila in enumerate(reader, start=2):
                    self.estadisticas['total_filas'] += 1
                    errores_fila = self._validar_fila(num_fila, fila, headers)

                    if errores_fila:
                        self.estadisticas['filas_con_error'] += 1
                        self.errores.extend(errores_fila)

        except Exception as e:
            logger.error(f"Error al procesar archivo: {e}")
            raise

        resultado = {
            'archivo': archivo_csv,
            'fecha_analisis': datetime.now().isoformat(),
            'estadisticas': self.estadisticas,
            'errores': self.errores,
            'columnas': headers
        }

        logger.info(f"Analisis completado. Filas: {self.estadisticas['total_filas']}, "
                   f"Con errores: {self.estadisticas['filas_con_error']}")

        return resultado

    def _validar_fila(self, num_fila: int, fila: Dict, headers: List[str]) -> List[Dict]:
        """Valida una fila y retorna lista de errores."""
        errores = []

        for campo, valor in fila.items():
            # Validar campos vacios
            if valor is None or str(valor).strip() == '':
                if self._es_campo_obligatorio(campo):
                    errores.append(self._crear_error(
                        num_fila, campo, valor, 'CAMPO_VACIO',
                        f'Campo obligatorio {campo} esta vacio'
                    ))
            else:
                valor = str(valor).strip()

                # Validar espacios al inicio/fin
                if str(fila[campo]) != valor:
                    errores.append(self._crear_error(
                        num_fila, campo, fila[campo], 'ESPACIOS_EXTRA',
                        'Tiene espacios al inicio o fin'
                    ))

                # Validar longitud maxima
                longitud_max = self._obtener_longitud_max(campo)
                if longitud_max and len(valor) > longitud_max:
                    errores.append(self._crear_error(
                        num_fila, campo, valor, 'LONGITUD_EXCEDIDA',
                        f'Excede longitud maxima de {longitud_max}'
                    ))

                # Validar caracteres especiales problematicos
                caracteres_problematicos = self._detectar_caracteres_problematicos(valor)
                if caracteres_problematicos:
                    errores.append(self._crear_error(
                        num_fila, campo, valor, 'CARACTERES_INVALIDOS',
                        f'Contiene caracteres problematicos: {caracteres_problematicos}'
                    ))

        return errores

    def _crear_error(self, fila: int, campo: str, valor: Any,
                     tipo: str, mensaje: str) -> Dict:
        """Crea registro de error estandarizado."""
        # Actualizar estadisticas
        self.estadisticas['errores_por_campo'][campo] = \
            self.estadisticas['errores_por_campo'].get(campo, 0) + 1
        self.estadisticas['errores_por_tipo'][tipo] = \
            self.estadisticas['errores_por_tipo'].get(tipo, 0) + 1

        return {
            'fila': fila,
            'campo': campo,
            'valor_actual': valor,
            'tipo_error': tipo,
            'mensaje': mensaje,
            'accion_sugerida': self._sugerir_accion(tipo, valor)
        }

    def _es_campo_obligatorio(self, campo: str) -> bool:
        """Verifica si un campo es obligatorio."""
        campos_obligatorios = self.config.get('validaciones', {}).get('campos_obligatorios', [])
        return campo in campos_obligatorios

    def _obtener_longitud_max(self, campo: str) -> Optional[int]:
        """Obtiene longitud maxima para un campo."""
        longitudes = self.config.get('validaciones', {}).get('longitudes_maximas', {})
        return longitudes.get(campo)

    def _detectar_caracteres_problematicos(self, valor: str) -> str:
        """Detecta caracteres que pueden causar problemas."""
        problematicos = []
        for char in valor:
            if ord(char) < 32 and char not in '\t\n\r':
                problematicos.append(f'\\x{ord(char):02x}')
            elif ord(char) > 127 and ord(char) < 160:
                problematicos.append(f'\\x{ord(char):02x}')
        return ', '.join(problematicos) if problematicos else ''

    def _sugerir_accion(self, tipo_error: str, valor: Any) -> str:
        """Sugiere accion correctiva basada en tipo de error."""
        acciones = {
            'CAMPO_VACIO': 'Completar valor o verificar si es requerido',
            'ESPACIOS_EXTRA': 'Aplicar TRIM() en base de datos',
            'LONGITUD_EXCEDIDA': 'Truncar o revisar campo en origen',
            'CARACTERES_INVALIDOS': 'Limpiar caracteres de control',
            'FORMATO_FECHA': 'Convertir a formato estandar YYYY-MM-DD',
            'VALOR_INVALIDO': 'Corregir valor segun catalogo permitido'
        }
        return acciones.get(tipo_error, 'Revisar manualmente')

    def exportar_errores_csv(self, ruta_salida: str):
        """Exporta errores a archivo CSV para TICS."""
        with open(ruta_salida, 'w', newline='', encoding='utf-8') as f:
            if not self.errores:
                f.write("Sin errores encontrados\n")
                return

            writer = csv.DictWriter(f, fieldnames=[
                'fila', 'campo', 'valor_actual', 'tipo_error',
                'mensaje', 'accion_sugerida'
            ])
            writer.writeheader()
            writer.writerows(self.errores)

        logger.info(f"Errores exportados a: {ruta_salida}")

    def generar_resumen(self) -> str:
        """Genera resumen textual del analisis."""
        resumen = []
        resumen.append("=" * 60)
        resumen.append("RESUMEN DE ANALISIS RCE")
        resumen.append("=" * 60)
        resumen.append(f"Total de filas analizadas: {self.estadisticas['total_filas']}")
        resumen.append(f"Filas con errores: {self.estadisticas['filas_con_error']}")
        resumen.append("")
        resumen.append("ERRORES POR TIPO:")
        for tipo, cantidad in sorted(self.estadisticas['errores_por_tipo'].items(),
                                     key=lambda x: -x[1]):
            resumen.append(f"  - {tipo}: {cantidad}")
        resumen.append("")
        resumen.append("ERRORES POR CAMPO:")
        for campo, cantidad in sorted(self.estadisticas['errores_por_campo'].items(),
                                      key=lambda x: -x[1]):
            resumen.append(f"  - {campo}: {cantidad}")
        resumen.append("=" * 60)

        return "\n".join(resumen)


def main():
    """Punto de entrada principal."""
    if len(sys.argv) < 2:
        print("Uso: python csv_analyzer.py <archivo.csv> [--config config.json]")
        sys.exit(1)

    archivo = sys.argv[1]
    config = None

    if '--config' in sys.argv:
        idx = sys.argv.index('--config')
        if idx + 1 < len(sys.argv):
            config = sys.argv[idx + 1]

    analyzer = CSVAnalyzer(config)
    resultado = analyzer.analizar_archivo(archivo)

    # Generar salidas
    nombre_base = Path(archivo).stem
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Exportar errores
    ruta_errores = f"../../output/listados_tics/{nombre_base}_errores_{timestamp}.csv"
    analyzer.exportar_errores_csv(ruta_errores)

    # Mostrar resumen
    print(analyzer.generar_resumen())

    # Guardar resultado JSON
    ruta_json = f"../../output/listados_tics/{nombre_base}_resultado_{timestamp}.json"
    with open(ruta_json, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print(f"\nArchivos generados:")
    print(f"  - Errores CSV: {ruta_errores}")
    print(f"  - Resultado JSON: {ruta_json}")


if __name__ == '__main__':
    main()
