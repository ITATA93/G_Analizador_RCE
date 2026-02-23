"""
Analizador de datos ALMA vs Funcionarios/Medicos
Cruza datos de personal con usuarios ALMA para detectar inconsistencias
"""

import pandas as pd
import numpy as np
import re
import unicodedata
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
import json

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ALMAAnalyzer:
    """Analizador de cruce ALMA vs Personal."""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent.parent
        self.data = {}
        self.resultados = {
            'funcionarios_sin_alma': [],
            'funcionarios_en_alma': [],
            'perfil_incorrecto': [],
            'grupo_incorrecto': [],
            'local_incorrecto': [],
            'problemas_caracteres': [],
            'usuarios_inactivos': [],
            'medicos_sin_flag_doctor': [],
            'estadisticas': {}
        }

    def cargar_datos(self):
        """Carga todos los CSVs necesarios."""
        logger.info("Cargando datos...")

        # Rutas
        alma_path = self.base_path / 'data' / 'csv_entrada' / 'Usuarios'
        data_path = self.base_path / 'data'

        # Cargar CSVs de ALMA
        archivos_alma = {
            'usuarios': '01_Usuarios.csv',
            'grupos': '02_Grupos.csv',
            'perfiles': '03_Perfiles.csv',
            'profesionales': '04_Profesionales.csv',
            'especialidades': '05_Especialidades.csv',
            'hospitales': '06_Hospitales.csv',
            'usuarios_grupos': '07_Usuarios_Grupos.csv',
            'usuarios_perfiles': '08_Usuarios_Perfiles.csv',
            'prof_especialidades': '09_Profesionales_Especialidades.csv',
            'prof_usuarios': '10_Profesionales_Usuarios.csv',
            'especialistas_estado': '11_Especialistas_Estado.csv',
        }

        for nombre, archivo in archivos_alma.items():
            ruta = alma_path / archivo
            if ruta.exists():
                self.data[nombre] = self._cargar_csv(ruta)
                logger.info(f"  {nombre}: {len(self.data[nombre])} registros")

        # Cargar Funcionarios
        func_path = data_path / 'Funcionarios.csv'
        if func_path.exists():
            self.data['funcionarios'] = self._cargar_csv(func_path)
            logger.info(f"  funcionarios: {len(self.data['funcionarios'])} registros")

        # Cargar Medicos
        medicos_path = list(data_path.glob('*MEDICOS*.csv'))
        if medicos_path:
            self.data['medicos'] = self._cargar_csv(medicos_path[0])
            logger.info(f"  medicos: {len(self.data['medicos'])} registros")

        logger.info("Datos cargados.")

    def _cargar_csv(self, ruta: Path) -> pd.DataFrame:
        """Carga CSV con deteccion de encoding y separador."""
        # Intentar diferentes encodings (latin-1 primero para archivos de Personal)
        encodings = ['latin-1', 'utf-8-sig', 'utf-8', 'cp1252']

        for enc in encodings:
            try:
                df = pd.read_csv(ruta, sep=';', encoding=enc, dtype=str)
                df = df.fillna('')
                # Normalizar nombres de columnas (quitar acentos, etc.)
                df.columns = [self._normalizar_columna(c) for c in df.columns]
                return df
            except Exception:
                continue

        raise ValueError(f"No se pudo cargar {ruta}")

    def _normalizar_columna(self, nombre: str) -> str:
        """Normaliza nombre de columna quitando acentos y caracteres especiales."""
        if not nombre:
            return ''
        # Mapeo de caracteres con problemas de encoding
        reemplazos = {
            'ó': 'o', 'Ó': 'O', 'í': 'i', 'Í': 'I',
            'á': 'a', 'Á': 'A', 'é': 'e', 'É': 'E',
            'ú': 'u', 'Ú': 'U', 'ñ': 'n', 'Ñ': 'N',
            'ü': 'u', 'Ü': 'U',
        }
        resultado = nombre.strip()
        for orig, reempl in reemplazos.items():
            resultado = resultado.replace(orig, reempl)
        # Quitar caracteres no ASCII restantes
        resultado = ''.join(c if ord(c) < 128 else '' for c in resultado)
        return resultado

    def _limpiar_texto(self, texto: str) -> str:
        """Limpia texto de caracteres problematicos."""
        if not texto:
            return ''
        # Normalizar unicode
        texto = unicodedata.normalize('NFKC', str(texto))
        # Quitar espacios extra
        texto = texto.strip()
        return texto

    def _normalizar_rut(self, rut: str, dv: str = None) -> str:
        """Normaliza RUT a formato sin puntos ni guion."""
        if not rut:
            return ''

        rut = str(rut).strip()

        # Si viene con DV separado
        if dv:
            dv = str(dv).strip().upper()
            return f"{rut}-{dv}"

        # Si ya tiene guion, extraer partes
        if '-' in rut:
            partes = rut.replace('.', '').split('-')
            if len(partes) == 2:
                return f"{partes[0]}-{partes[1].upper()}"

        # Limpiar puntos y espacios
        rut = rut.replace('.', '').replace(' ', '')
        return rut.upper()

    def _detectar_caracteres_problematicos(self, texto: str) -> List[str]:
        """Detecta caracteres que pueden causar problemas."""
        problemas = []
        if not texto:
            return problemas

        texto = str(texto)

        # Caracteres de control
        for i, char in enumerate(texto):
            code = ord(char)
            if code < 32 and char not in '\t\n\r':
                problemas.append(f"Caracter control en pos {i}: \\x{code:02x}")
            elif code > 127:
                # Verificar si es un caracter valido latin
                try:
                    char.encode('latin-1')
                except UnicodeEncodeError:
                    # Es unicode especial, puede causar problemas
                    if char not in 'áéíóúÁÉÍÓÚñÑüÜ':
                        problemas.append(f"Caracter especial en pos {i}: '{char}' (U+{code:04X})")

        return problemas

    def analizar_cruce_funcionarios_alma(self):
        """Analiza cruce entre funcionarios y usuarios ALMA."""
        logger.info("Analizando cruce Funcionarios vs ALMA...")

        if 'funcionarios' not in self.data or 'usuarios' not in self.data:
            logger.error("Faltan datos de funcionarios o usuarios")
            return

        funcionarios = self.data['funcionarios'].copy()
        usuarios = self.data['usuarios'].copy()

        # Normalizar RUTs
        funcionarios['rut_norm'] = funcionarios.apply(
            lambda r: self._normalizar_rut(r.get('Rut', ''), r.get('Dv', '')),
            axis=1
        )

        # En usuarios, el RUT parece estar en "Iniciales"
        usuarios['rut_norm'] = usuarios['Iniciales'].apply(
            lambda x: self._normalizar_rut(x) if x else ''
        )

        # Crear diccionario de usuarios por RUT
        usuarios_por_rut = {}
        for _, row in usuarios.iterrows():
            rut = row['rut_norm']
            if rut:
                if rut not in usuarios_por_rut:
                    usuarios_por_rut[rut] = []
                usuarios_por_rut[rut].append(row.to_dict())

        # Analizar cada funcionario
        # Nombres de columnas normalizados (sin acentos gracias a _normalizar_columna)
        for _, func in funcionarios.iterrows():
            rut = func['rut_norm']
            nombre = func.get('Nombre Funcionario', '')
            cargo = func.get('Descripcion Cargo', '')
            unidad = func.get('Descripcion Unidad', '')
            planta = func.get('Descripcion Planta', '')

            # Detectar problemas de caracteres en nombre
            problemas_chars = self._detectar_caracteres_problematicos(nombre)
            if problemas_chars:
                self.resultados['problemas_caracteres'].append({
                    'rut': rut,
                    'nombre': nombre,
                    'campo': 'Nombre',
                    'problemas': problemas_chars
                })

            # Buscar en ALMA
            if rut in usuarios_por_rut:
                usuarios_func = usuarios_por_rut[rut]
                for usuario in usuarios_func:
                    self.resultados['funcionarios_en_alma'].append({
                        'rut': rut,
                        'nombre_personal': nombre,
                        'nombre_alma': usuario.get('Nombre', ''),
                        'cargo': cargo,
                        'unidad': unidad,
                        'planta': planta,
                        'activo_alma': usuario.get('Activo', ''),
                        'es_doctor_alma': usuario.get('EsDoctor', ''),
                        'perfil_id': usuario.get('PerfilID', ''),
                        'grupo_id': usuario.get('GrupoID', ''),
                        'hospital_id': usuario.get('HospitalID', ''),
                        'ultimo_login': usuario.get('UltimoLogin_Fecha', '')
                    })

                    # Verificar si esta inactivo
                    if usuario.get('Activo', '').upper() != 'Y':
                        self.resultados['usuarios_inactivos'].append({
                            'rut': rut,
                            'nombre': nombre,
                            'cargo': cargo,
                            'activo_alma': usuario.get('Activo', ''),
                            'ultimo_login': usuario.get('UltimoLogin_Fecha', '')
                        })

                    # Verificar si es medico pero no tiene flag doctor
                    if planta == 'MEDICOS' and usuario.get('EsDoctor', '').upper() != 'Y':
                        self.resultados['medicos_sin_flag_doctor'].append({
                            'rut': rut,
                            'nombre': nombre,
                            'cargo': cargo,
                            'es_doctor_alma': usuario.get('EsDoctor', ''),
                            'perfil_id': usuario.get('PerfilID', '')
                        })
            else:
                self.resultados['funcionarios_sin_alma'].append({
                    'rut': rut,
                    'nombre': nombre,
                    'cargo': cargo,
                    'unidad': unidad,
                    'planta': planta
                })

        # Estadisticas
        self.resultados['estadisticas']['total_funcionarios'] = len(funcionarios)
        self.resultados['estadisticas']['funcionarios_en_alma'] = len(self.resultados['funcionarios_en_alma'])
        self.resultados['estadisticas']['funcionarios_sin_alma'] = len(self.resultados['funcionarios_sin_alma'])
        self.resultados['estadisticas']['usuarios_inactivos'] = len(self.resultados['usuarios_inactivos'])
        self.resultados['estadisticas']['problemas_caracteres'] = len(self.resultados['problemas_caracteres'])
        self.resultados['estadisticas']['medicos_sin_flag'] = len(self.resultados['medicos_sin_flag_doctor'])

        logger.info(f"  Funcionarios en ALMA: {self.resultados['estadisticas']['funcionarios_en_alma']}")
        logger.info(f"  Funcionarios SIN ALMA: {self.resultados['estadisticas']['funcionarios_sin_alma']}")

    def analizar_perfiles_por_cargo(self):
        """Analiza si los perfiles asignados corresponden al cargo."""
        logger.info("Analizando perfiles por cargo...")

        if 'perfiles' not in self.data:
            return

        # Mapeo de cargos a perfiles esperados (ajustar segun reglas del hospital)
        mapeo_cargo_perfil = {
            'MEDICO CIRUJANO': ['Med', 'Doc', 'Cir'],
            'ENFERMERO(A)': ['Enf', 'Nur'],
            'TECNICO EN ENFERMERIA': ['Ten', 'Tec'],
            'KINESIOLOGO(A)': ['Kin', 'Kine'],
            'MATRONA': ['Mat', 'Mid'],
            'PSICOLOGO(A)': ['Psi', 'Psico'],
            'NUTRICIONISTA': ['Nut', 'Nutr'],
            'FONOAUDIOLOGO(A)': ['Fono'],
            'TECNOLOGO MEDICO': ['Tec', 'TM'],
            'QUIMICO FARMACEUTICO': ['QF', 'Farm'],
            'ADMINISTRATIVO': ['Adm', 'Admin'],
        }

        perfiles = self.data['perfiles'].set_index('ID')['Codigo'].to_dict()

        for registro in self.resultados['funcionarios_en_alma']:
            cargo = registro['cargo']
            perfil_id = registro['perfil_id']

            if perfil_id and perfil_id in perfiles:
                codigo_perfil = perfiles[perfil_id]

                # Buscar si el cargo tiene perfiles esperados
                for cargo_key, prefijos in mapeo_cargo_perfil.items():
                    if cargo_key in cargo.upper():
                        # Verificar si el perfil coincide
                        perfil_ok = any(p.lower() in codigo_perfil.lower() for p in prefijos)
                        if not perfil_ok:
                            self.resultados['perfil_incorrecto'].append({
                                'rut': registro['rut'],
                                'nombre': registro['nombre_personal'],
                                'cargo': cargo,
                                'perfil_actual': codigo_perfil,
                                'perfiles_esperados': prefijos
                            })
                        break

        self.resultados['estadisticas']['perfiles_incorrectos'] = len(self.resultados['perfil_incorrecto'])
        logger.info(f"  Perfiles posiblemente incorrectos: {self.resultados['estadisticas']['perfiles_incorrectos']}")

    def analizar_grupos_seguridad(self):
        """Analiza grupos de seguridad asignados."""
        logger.info("Analizando grupos de seguridad...")

        if 'usuarios_grupos' not in self.data:
            return

        # Crear diccionario de grupos por usuario
        grupos_por_usuario = {}
        for _, row in self.data['usuarios_grupos'].iterrows():
            usuario_nombre = row.get('UsuarioNombre', '')  # Esto es el RUT
            grupo_desc = row.get('GrupoDesc', '')

            if usuario_nombre:
                rut = self._normalizar_rut(usuario_nombre)
                if rut not in grupos_por_usuario:
                    grupos_por_usuario[rut] = []
                grupos_por_usuario[rut].append(grupo_desc)

        # Agregar info de grupos a funcionarios en ALMA
        for registro in self.resultados['funcionarios_en_alma']:
            rut = registro['rut']
            registro['grupos'] = grupos_por_usuario.get(rut, [])

    def detectar_problemas_caracteres_alma(self):
        """Detecta problemas de caracteres en datos ALMA."""
        logger.info("Detectando problemas de caracteres en ALMA...")

        campos_a_revisar = [
            ('usuarios', 'Nombre'),
            ('profesionales', 'NombreCompleto'),
            ('profesionales', 'Nombre'),
            ('profesionales', 'Apellido'),
            ('grupos', 'Descripcion'),
            ('perfiles', 'Descripcion'),
            ('especialidades', 'Descripcion'),
        ]

        for tabla, campo in campos_a_revisar:
            if tabla not in self.data:
                continue

            df = self.data[tabla]
            if campo not in df.columns:
                continue

            for idx, valor in df[campo].items():
                if not valor:
                    continue

                problemas = self._detectar_caracteres_problematicos(valor)
                if problemas:
                    self.resultados['problemas_caracteres'].append({
                        'tabla': tabla,
                        'campo': campo,
                        'registro_idx': idx,
                        'valor': valor,
                        'problemas': problemas
                    })

    def generar_reporte(self, output_path: str = None) -> Dict:
        """Genera reporte completo de analisis."""
        if not output_path:
            output_path = self.base_path / 'output' / 'listados_tics'

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 1. Funcionarios sin ALMA
        if self.resultados['funcionarios_sin_alma']:
            df = pd.DataFrame(self.resultados['funcionarios_sin_alma'])
            df.to_csv(output_path / f'funcionarios_sin_alma_{timestamp}.csv',
                     index=False, sep=';', encoding='utf-8-sig')

        # 2. Funcionarios en ALMA (para revision)
        if self.resultados['funcionarios_en_alma']:
            df = pd.DataFrame(self.resultados['funcionarios_en_alma'])
            df.to_csv(output_path / f'funcionarios_en_alma_{timestamp}.csv',
                     index=False, sep=';', encoding='utf-8-sig')

        # 3. Usuarios inactivos
        if self.resultados['usuarios_inactivos']:
            df = pd.DataFrame(self.resultados['usuarios_inactivos'])
            df.to_csv(output_path / f'usuarios_inactivos_{timestamp}.csv',
                     index=False, sep=';', encoding='utf-8-sig')

        # 4. Medicos sin flag doctor
        if self.resultados['medicos_sin_flag_doctor']:
            df = pd.DataFrame(self.resultados['medicos_sin_flag_doctor'])
            df.to_csv(output_path / f'medicos_sin_flag_doctor_{timestamp}.csv',
                     index=False, sep=';', encoding='utf-8-sig')

        # 5. Perfiles incorrectos
        if self.resultados['perfil_incorrecto']:
            df = pd.DataFrame(self.resultados['perfil_incorrecto'])
            df.to_csv(output_path / f'perfiles_incorrectos_{timestamp}.csv',
                     index=False, sep=';', encoding='utf-8-sig')

        # 6. Problemas de caracteres
        if self.resultados['problemas_caracteres']:
            df = pd.DataFrame(self.resultados['problemas_caracteres'])
            df.to_csv(output_path / f'problemas_caracteres_{timestamp}.csv',
                     index=False, sep=';', encoding='utf-8-sig')

        # 7. Resumen JSON
        with open(output_path / f'resumen_analisis_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(self.resultados['estadisticas'], f, indent=2, ensure_ascii=False)

        # 8. Resumen texto
        resumen = self._generar_resumen_texto()
        with open(output_path / f'resumen_analisis_{timestamp}.txt', 'w', encoding='utf-8') as f:
            f.write(resumen)

        logger.info(f"Reportes generados en: {output_path}")
        return self.resultados['estadisticas']

    def _generar_resumen_texto(self) -> str:
        """Genera resumen en texto."""
        stats = self.resultados['estadisticas']

        lineas = [
            "=" * 70,
            "RESUMEN ANALISIS ALMA vs PERSONAL",
            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 70,
            "",
            "CRUCE FUNCIONARIOS - ALMA:",
            "-" * 40,
            f"  Total funcionarios analizados:    {stats.get('total_funcionarios', 0):,}",
            f"  Funcionarios CON usuario ALMA:    {stats.get('funcionarios_en_alma', 0):,}",
            f"  Funcionarios SIN usuario ALMA:    {stats.get('funcionarios_sin_alma', 0):,}",
            "",
            "PROBLEMAS DETECTADOS:",
            "-" * 40,
            f"  Usuarios inactivos en ALMA:       {stats.get('usuarios_inactivos', 0):,}",
            f"  Medicos sin flag EsDoctor:        {stats.get('medicos_sin_flag', 0):,}",
            f"  Perfiles posiblemente incorrectos:{stats.get('perfiles_incorrectos', 0):,}",
            f"  Registros con problemas chars:    {stats.get('problemas_caracteres', 0):,}",
            "",
            "ARCHIVOS GENERADOS:",
            "-" * 40,
            "  - funcionarios_sin_alma_*.csv",
            "  - funcionarios_en_alma_*.csv",
            "  - usuarios_inactivos_*.csv",
            "  - medicos_sin_flag_doctor_*.csv",
            "  - perfiles_incorrectos_*.csv",
            "  - problemas_caracteres_*.csv",
            "",
            "=" * 70,
        ]

        return "\n".join(lineas)

    def ejecutar_analisis_completo(self):
        """Ejecuta analisis completo."""
        logger.info("=" * 60)
        logger.info("INICIANDO ANALISIS COMPLETO ALMA vs PERSONAL")
        logger.info("=" * 60)

        self.cargar_datos()
        self.analizar_cruce_funcionarios_alma()
        self.analizar_perfiles_por_cargo()
        self.analizar_grupos_seguridad()
        self.detectar_problemas_caracteres_alma()

        stats = self.generar_reporte()

        print(self._generar_resumen_texto())

        return stats


def main():
    """Punto de entrada."""
    import sys

    base_path = None
    if len(sys.argv) > 1:
        base_path = sys.argv[1]

    analyzer = ALMAAnalyzer(base_path)
    analyzer.ejecutar_analisis_completo()


if __name__ == '__main__':
    main()
