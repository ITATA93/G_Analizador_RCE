"""
Sistema de logging centralizado para Analizador RCE
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class RCELogger:
    """Logger centralizado con rotacion y multiples destinos."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if RCELogger._initialized:
            return

        self.logs_dir = Path(__file__).parent.parent.parent / 'logs'
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Crear subdirectorios de logs
        (self.logs_dir / 'analisis').mkdir(exist_ok=True)
        (self.logs_dir / 'correcciones').mkdir(exist_ok=True)
        (self.logs_dir / 'reportes_tics').mkdir(exist_ok=True)

        self.loggers = {}
        RCELogger._initialized = True

    def get_logger(self, nombre: str, categoria: str = 'analisis') -> logging.Logger:
        """
        Obtiene logger configurado.

        Args:
            nombre: Nombre del logger
            categoria: Subdirectorio de logs (analisis, correcciones, reportes_tics)
        """
        logger_key = f"{categoria}_{nombre}"

        if logger_key in self.loggers:
            return self.loggers[logger_key]

        logger = logging.getLogger(logger_key)
        logger.setLevel(logging.DEBUG)

        # Evitar duplicar handlers
        if logger.handlers:
            return logger

        # Formato de log
        formato = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Handler para archivo con rotacion
        fecha = datetime.now().strftime('%Y%m%d')
        archivo_log = self.logs_dir / categoria / f'{nombre}_{fecha}.log'

        file_handler = RotatingFileHandler(
            archivo_log,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formato)

        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formato)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        self.loggers[logger_key] = logger
        return logger

    def log_inicio_analisis(self, archivo: str, logger: logging.Logger):
        """Log estandar de inicio de analisis."""
        logger.info("=" * 60)
        logger.info(f"INICIO ANALISIS: {archivo}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 60)

    def log_fin_analisis(self, estadisticas: dict, logger: logging.Logger):
        """Log estandar de fin de analisis."""
        logger.info("-" * 60)
        logger.info("RESUMEN ANALISIS:")
        for key, value in estadisticas.items():
            logger.info(f"  {key}: {value}")
        logger.info("=" * 60)

    def log_error_critico(self, mensaje: str, excepcion: Optional[Exception],
                          logger: logging.Logger):
        """Log de error critico con stack trace."""
        logger.error("!" * 60)
        logger.error(f"ERROR CRITICO: {mensaje}")
        if excepcion:
            logger.exception(excepcion)
        logger.error("!" * 60)


# Singleton global
rce_logger = RCELogger()


def get_logger(nombre: str, categoria: str = 'analisis') -> logging.Logger:
    """Funcion helper para obtener logger."""
    return rce_logger.get_logger(nombre, categoria)
