"""
Cargador de datos CSV a formato SQL/estructurado
Normaliza y prepara datos para importacion
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class DataLoader:
    """Carga y normaliza datos CSV para SQL."""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent.parent
        self.data = {}

    def _normalizar_rut(self, rut: str, dv: str = None) -> str:
        """Normaliza RUT a formato XXXXXXXX-X."""
        if not rut:
            return ''

        rut = str(rut).strip()

        if dv:
            dv = str(dv).strip().upper()
            # Limpiar rut de puntos
            rut = rut.replace('.', '').replace(' ', '')
            return f"{rut}-{dv}"

        # Si ya tiene guion
        if '-' in rut:
            partes = rut.replace('.', '').split('-')
            if len(partes) == 2:
                return f"{partes[0]}-{partes[1].upper()}"

        return rut.replace('.', '').upper()

    def _limpiar_fecha(self, fecha: str) -> Optional[str]:
        """Convierte fecha a formato SQL (YYYY-MM-DD)."""
        if not fecha:
            return None

        fecha = str(fecha).strip()

        # Formatos comunes
        formatos = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%d',
            '%Y/%m/%d',
        ]

        for fmt in formatos:
            try:
                dt = datetime.strptime(fecha, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        # Intentar con numero Excel
        try:
            dias = int(float(fecha))
            if 30000 < dias < 80000:  # Rango razonable Excel
                dt = datetime(1899, 12, 30) + pd.Timedelta(days=dias)
                return dt.strftime('%Y-%m-%d')
        except:
            pass

        return None

    def _cargar_csv(self, ruta: Path) -> pd.DataFrame:
        """Carga CSV con deteccion de encoding."""
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']

        for enc in encodings:
            try:
                df = pd.read_csv(ruta, sep=';', encoding=enc, dtype=str)
                df = df.fillna('')
                return df
            except:
                continue

        raise ValueError(f"No se pudo cargar: {ruta}")

    def cargar_y_normalizar_alma(self) -> Dict[str, pd.DataFrame]:
        """Carga y normaliza todos los CSVs de ALMA."""
        logger.info("Cargando datos ALMA...")

        alma_path = self.base_path / 'data' / 'csv_entrada' / 'Usuarios'
        resultado = {}

        # 01_Usuarios
        df = self._cargar_csv(alma_path / '01_Usuarios.csv')
        df['rut'] = df['Iniciales'].apply(self._normalizar_rut)
        df['ultimo_login_fecha'] = df['UltimoLogin_Fecha'].apply(self._limpiar_fecha)
        resultado['usuarios'] = df.rename(columns={
            'ID': 'id', 'Nombre': 'nombre', 'LoginID': 'login_id',
            'Activo': 'activo', 'EsDoctor': 'es_doctor', 'EsEnfermera': 'es_enfermera',
            'GrupoID': 'grupo_id', 'PerfilID': 'perfil_id',
            'CareProvID': 'care_prov_id', 'HospitalID': 'hospital_id',
            'Email': 'email', 'Movil': 'movil'
        })
        logger.info(f"  Usuarios: {len(df)} registros")

        # 02_Grupos
        df = self._cargar_csv(alma_path / '02_Grupos.csv')
        df['fecha_desde'] = df['FechaDesde'].apply(self._limpiar_fecha)
        df['fecha_hasta'] = df['FechaHasta'].apply(self._limpiar_fecha)
        resultado['grupos'] = df.rename(columns={
            'ID': 'id', 'Descripcion': 'descripcion', 'NivelSeguridad': 'nivel_seguridad'
        })
        logger.info(f"  Grupos: {len(df)} registros")

        # 03_Perfiles
        df = self._cargar_csv(alma_path / '03_Perfiles.csv')
        df['fecha_desde'] = df['FechaDesde'].apply(self._limpiar_fecha)
        df['fecha_hasta'] = df['FechaHasta'].apply(self._limpiar_fecha)
        resultado['perfiles'] = df.rename(columns={
            'ID': 'id', 'Codigo': 'codigo', 'Descripcion': 'descripcion'
        })
        logger.info(f"  Perfiles: {len(df)} registros")

        # 04_Profesionales
        df = self._cargar_csv(alma_path / '04_Profesionales.csv')
        df['rut'] = df['NombreCompleto'].apply(self._normalizar_rut)
        resultado['profesionales'] = df.rename(columns={
            'ID': 'id', 'Codigo': 'codigo', 'Nombre': 'nombre', 'Apellido': 'apellido',
            'Activo': 'activo', 'EsEspecialista': 'es_especialista',
            'EsCirujano': 'es_cirujano', 'EsAnestesista': 'es_anestesista',
            'EsRadiologo': 'es_radiologo', 'EspecialidadID': 'especialidad_id',
            'NumRegistro': 'num_registro', 'Email': 'email', 'Movil': 'movil'
        })
        logger.info(f"  Profesionales: {len(df)} registros")

        # 05_Especialidades
        df = self._cargar_csv(alma_path / '05_Especialidades.csv')
        resultado['especialidades'] = df.rename(columns={
            'ID': 'id', 'Codigo': 'codigo', 'Descripcion': 'descripcion'
        })
        logger.info(f"  Especialidades: {len(df)} registros")

        # 06_Hospitales
        df = self._cargar_csv(alma_path / '06_Hospitales.csv')
        resultado['hospitales'] = df.rename(columns={
            'ID': 'id', 'Codigo': 'codigo', 'Descripcion': 'descripcion'
        })
        logger.info(f"  Hospitales: {len(df)} registros")

        # 07_Usuarios_Grupos
        df = self._cargar_csv(alma_path / '07_Usuarios_Grupos.csv')
        df['usuario_rut'] = df['UsuarioNombre'].apply(self._normalizar_rut)
        resultado['usuarios_grupos'] = df.rename(columns={
            'UsuarioID': 'usuario_id', 'Activo': 'activo',
            'GrupoID': 'grupo_id', 'GrupoDesc': 'grupo_desc'
        })
        logger.info(f"  Usuarios_Grupos: {len(df)} registros")

        # 08_Usuarios_Perfiles
        df = self._cargar_csv(alma_path / '08_Usuarios_Perfiles.csv')
        df['usuario_rut'] = df['UsuarioNombre'].apply(self._normalizar_rut)
        resultado['usuarios_perfiles'] = df.rename(columns={
            'UsuarioID': 'usuario_id', 'Activo': 'activo',
            'PerfilID': 'perfil_id', 'PerfilDesc': 'perfil_desc'
        })
        logger.info(f"  Usuarios_Perfiles: {len(df)} registros")

        self.data['alma'] = resultado
        return resultado

    def cargar_y_normalizar_personal(self) -> Dict[str, pd.DataFrame]:
        """Carga y normaliza datos de Personal."""
        logger.info("Cargando datos Personal...")

        data_path = self.base_path / 'data'
        resultado = {}

        # Funcionarios
        func_path = data_path / 'Funcionarios.csv'
        if func_path.exists():
            df = self._cargar_csv(func_path)
            df['rut'] = df.apply(lambda r: self._normalizar_rut(r['Rut'], r['Dv']), axis=1)
            df['fecha_nacimiento'] = df['Fecha Nacimiento'].apply(self._limpiar_fecha)
            resultado['funcionarios'] = df.rename(columns={
                'Rut': 'rut_numero', 'Dv': 'rut_dv',
                'Nombre Funcionario': 'nombre',
                'Descripcion Planta': 'planta',
                'Descripcion Calidad Juridica': 'calidad_juridica',
                'Grado': 'grado', 'Genero': 'genero',
                'Nacionalidad': 'nacionalidad', 'Ley': 'ley',
                'Descripcion Establecimiento': 'establecimiento',
                'Edad': 'edad',
                'Descripcion Unidad': 'unidad',
                'Descripcion Cargo': 'cargo',
                'Transitorio': 'transitorio'
            })
            logger.info(f"  Funcionarios: {len(df)} registros")

        # Medicos
        medicos_path = list(data_path.glob('*MEDICOS*.csv'))
        if medicos_path:
            df = self._cargar_csv(medicos_path[0])
            df['rut'] = df.apply(lambda r: self._normalizar_rut(r['Rut'], r['Dv']), axis=1)
            df['fecha_nacimiento'] = df['Fecha Nacimiento'].apply(self._limpiar_fecha)
            resultado['medicos'] = df.rename(columns={
                'Rut': 'rut_numero', 'Dv': 'rut_dv',
                'Nombre Funcionario': 'nombre',
                'Descripcion Planta': 'planta',
                'Descripcion Calidad Juridica': 'calidad_juridica',
                'Grado': 'grado', 'Genero': 'genero',
                'Nacionalidad': 'nacionalidad', 'Ley': 'ley',
                'Numero horas': 'numero_horas',
                'Descripcion Unidad': 'unidad',
                'Descripcion Cargo': 'cargo',
                'Inscripcion superintendencia': 'inscripcion_sis',
                'Correl. Planta': 'correl_planta',
                'Transitorio': 'transitorio'
            })
            logger.info(f"  Medicos: {len(df)} registros")

        self.data['personal'] = resultado
        return resultado

    def exportar_sql_inserts(self, output_path: str = None):
        """Genera archivos SQL con INSERTs."""
        if not output_path:
            output_path = self.base_path / 'sql' / 'inserts'

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Generar INSERTs para cada tabla
        if 'alma' in self.data:
            for nombre, df in self.data['alma'].items():
                self._generar_insert(df, f'alma_{nombre}', output_path / f'insert_alma_{nombre}_{timestamp}.sql')

        if 'personal' in self.data:
            for nombre, df in self.data['personal'].items():
                self._generar_insert(df, f'personal_{nombre}', output_path / f'insert_personal_{nombre}_{timestamp}.sql')

        logger.info(f"INSERTs generados en: {output_path}")

    def _generar_insert(self, df: pd.DataFrame, tabla: str, ruta: Path):
        """Genera archivo SQL con INSERTs."""
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(f"-- INSERTs para {tabla}\n")
            f.write(f"-- Generado: {datetime.now().isoformat()}\n")
            f.write(f"-- Total registros: {len(df)}\n\n")

            columnas = [c for c in df.columns if not c.startswith('Unnamed')]

            for _, row in df.iterrows():
                valores = []
                for col in columnas:
                    val = row[col]
                    if val == '' or pd.isna(val):
                        valores.append('NULL')
                    elif isinstance(val, str):
                        val_escaped = val.replace("'", "''")
                        valores.append(f"'{val_escaped}'")
                    else:
                        valores.append(str(val))

                f.write(f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({', '.join(valores)});\n")

    def exportar_csv_normalizados(self, output_path: str = None):
        """Exporta CSVs normalizados listos para importar."""
        if not output_path:
            output_path = self.base_path / 'output' / 'csv_normalizados'

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if 'alma' in self.data:
            for nombre, df in self.data['alma'].items():
                ruta = output_path / f'alma_{nombre}_{timestamp}.csv'
                df.to_csv(ruta, index=False, sep=';', encoding='utf-8-sig')
                logger.info(f"  Exportado: {ruta.name}")

        if 'personal' in self.data:
            for nombre, df in self.data['personal'].items():
                ruta = output_path / f'personal_{nombre}_{timestamp}.csv'
                df.to_csv(ruta, index=False, sep=';', encoding='utf-8-sig')
                logger.info(f"  Exportado: {ruta.name}")

        logger.info(f"CSVs normalizados en: {output_path}")


def main():
    """Punto de entrada."""
    loader = DataLoader()
    loader.cargar_y_normalizar_alma()
    loader.cargar_y_normalizar_personal()
    loader.exportar_csv_normalizados()
    loader.exportar_sql_inserts()


if __name__ == '__main__':
    main()
