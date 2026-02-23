"""
Script principal - Analizador de Datos RCE
Interfaz de linea de comandos para analisis completo
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# Agregar path de scripts
sys.path.insert(0, str(Path(__file__).parent))

from analyzers.csv_analyzer import CSVAnalyzer
from validators.field_validator import FieldValidator
from reporters.tics_reporter import TICSReporter
from utils.logger import get_logger

logger = get_logger('main', 'analisis')


def analizar_csv(archivo: str, config: str = None):
    """Ejecuta analisis completo de un CSV."""
    logger.info(f"Iniciando analisis de: {archivo}")

    # Verificar archivo existe
    if not os.path.exists(archivo):
        # Buscar en carpeta de entrada
        ruta_entrada = Path(__file__).parent.parent / 'data' / 'csv_entrada' / archivo
        if ruta_entrada.exists():
            archivo = str(ruta_entrada)
        else:
            logger.error(f"Archivo no encontrado: {archivo}")
            print(f"Error: Archivo no encontrado: {archivo}")
            print(f"Asegurate de colocarlo en data/csv_entrada/")
            return None

    # Cargar config
    if not config:
        config = str(Path(__file__).parent.parent / 'config' / 'settings.json')

    # Analizar
    analyzer = CSVAnalyzer(config)
    resultado = analyzer.analizar_archivo(archivo)

    # Generar reportes
    reporter = TICSReporter(str(Path(__file__).parent.parent / 'output'))

    nombre_base = Path(archivo).stem

    # Generar listado TICS
    ruta_revision = reporter.generar_listado_para_revision(
        resultado['errores'], nombre_base
    )

    # Generar resumen
    ruta_resumen = reporter.generar_resumen_ejecutivo(
        resultado['estadisticas'], nombre_base
    )

    # Mostrar resumen en consola
    print(analyzer.generar_resumen())

    print(f"\nArchivos generados:")
    print(f"  - Listado revision: {ruta_revision}")
    print(f"  - Resumen: {ruta_resumen}")

    return resultado


def generar_sql(archivo: str, tabla: str):
    """Genera script SQL de correcciones."""
    # Primero analizar
    resultado = analizar_csv(archivo)

    if not resultado:
        return

    # Generar SQL
    reporter = TICSReporter(str(Path(__file__).parent.parent / 'output'))
    ruta_sql = reporter.generar_listado_correcciones_tabla(
        resultado['errores'], tabla
    )

    print(f"\nScript SQL generado: {ruta_sql}")


def listar_archivos():
    """Lista archivos CSV disponibles para analizar."""
    ruta_entrada = Path(__file__).parent.parent / 'data' / 'csv_entrada'

    print("\nArchivos CSV disponibles en data/csv_entrada/:")
    print("-" * 50)

    archivos = list(ruta_entrada.glob('*.csv'))
    if not archivos:
        print("  (ninguno)")
        print("\nColoca archivos CSV en data/csv_entrada/ para analizarlos.")
    else:
        for archivo in archivos:
            size = archivo.stat().st_size
            size_str = f"{size:,} bytes" if size < 1024*1024 else f"{size/1024/1024:.1f} MB"
            print(f"  - {archivo.name} ({size_str})")


def main():
    parser = argparse.ArgumentParser(
        description='Analizador de Datos RCE',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py analizar archivo.csv
  python main.py analizar archivo.csv --config mi_config.json
  python main.py sql archivo.csv --tabla nombre_tabla
  python main.py listar
        """
    )

    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponibles')

    # Comando: analizar
    parser_analizar = subparsers.add_parser('analizar', help='Analiza un archivo CSV')
    parser_analizar.add_argument('archivo', help='Archivo CSV a analizar')
    parser_analizar.add_argument('--config', '-c', help='Archivo de configuracion')

    # Comando: sql
    parser_sql = subparsers.add_parser('sql', help='Genera script SQL de correcciones')
    parser_sql.add_argument('archivo', help='Archivo CSV a analizar')
    parser_sql.add_argument('--tabla', '-t', required=True, help='Nombre de la tabla')

    # Comando: listar
    subparsers.add_parser('listar', help='Lista archivos CSV disponibles')

    args = parser.parse_args()

    if args.comando == 'analizar':
        analizar_csv(args.archivo, args.config)
    elif args.comando == 'sql':
        generar_sql(args.archivo, args.tabla)
    elif args.comando == 'listar':
        listar_archivos()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
