# G_Analizador_RCE

> Satellite project in the Antigravity ecosystem — Gemini CLI variant.

**Domain:** `01_HOSPITAL_PRIVADO`
**Status:** Active
**Orchestrator:** GEN_OS
**Prefix:** G_
**AG Counterpart:** `AG_Analizador_RCE`

## Proposito

Sistema para analizar datos extraidos del Resumen Clinico Electronico (RCE),
identificar campos con errores y generar listados de correcciones para el equipo TICS.

- Verificar campos que requieren correccion en exportaciones CSV
- Generar listados estructurados para el equipo TICS
- Identificar modificaciones necesarias en tablas o codigo
- Trabajar offline sin consultar la base LIVE directamente

## Arquitectura

```
G_Analizador_RCE/
├── .gemini/              # Configuracion Gemini CLI
├── .claude/              # Configuracion Claude Code
├── .subagents/           # Dispatch multi-vendor
├── config/               # Configuracion general y campos RCE
├── data/                 # CSV entrada / procesados / errores
├── scripts/              # Analizadores, validadores, reporteros
│   ├── analyzers/        # csv_analyzer.py
│   ├── validators/       # field_validator.py
│   └── reporters/        # tics_reporter.py
├── output/               # Listados TICS, scripts SQL, reportes
├── sql/                  # Consultas SQL de referencia
├── templates/            # Plantillas de reportes
├── logs/                 # Logs de analisis y correcciones
├── docs/                 # Documentacion y estandares
└── exports/              # Exportaciones de sesion
```

## Uso con Gemini CLI

```bash
# Analizar un CSV con Gemini CLI
gemini "Analiza el archivo data/csv_entrada/pacientes.csv e identifica errores"

# Validar campos especificos
gemini "Valida los campos RUT y fecha en data/csv_entrada/admisiones.csv"

# Generar reporte para TICS
gemini "Genera reporte de errores encontrados para el equipo TICS"

# Resumen ejecutivo de errores
gemini "Resume los errores detectados en la ultima corrida de analisis"
```

## Scripts

| Script | Ubicacion | Funcion |
|--------|-----------|---------|
| `csv_analyzer.py` | `scripts/analyzers/` | Analisis principal de CSV |
| `field_validator.py` | `scripts/validators/` | Validacion de campos (RUT, fechas, email) |
| `tics_reporter.py` | `scripts/reporters/` | Generacion de reportes para TICS |

## Configuracion

- `config/settings.json` -- Campos obligatorios, longitudes maximas
- `config/campos_rce.json` -- Reglas especificas por tabla y campo
- `GEMINI.md` -- Perfil del proyecto para Gemini CLI
- `CLAUDE.md` -- Instrucciones para Claude Code

## Tipos de Errores Detectados

| Codigo | Descripcion |
|--------|-------------|
| `CAMPO_VACIO` | Campo obligatorio sin valor |
| `RUT_INVALIDO` | Digito verificador incorrecto |
| `FORMATO_FECHA` | Fecha mal formateada |
| `VALOR_INVALIDO` | Valor fuera de catalogo |
| `CARACTERES_INVALIDOS` | Caracteres de control |

## Proyectos Relacionados

| Proyecto | Sinergia |
|----------|----------|
| `G_Consultas` | Queries SQL para TrakCare/ALMA |
| `G_Informatica_Medica` | Estandares de datos clinicos |
| `G_Hospital` | Documentacion de procesos |
