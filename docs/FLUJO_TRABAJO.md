# Flujo de Trabajo - Analizador RCE

## 1. Recepcion de Datos

### Origen de datos
- Exportaciones de RCE en formato CSV
- NO se consulta LIVE directamente
- Los datos se trabajan offline

### Preparacion
1. Recibir archivo CSV del solicitante
2. Colocar en `data/csv_entrada/`
3. Verificar encoding (preferir UTF-8)

## 2. Analisis Inicial

### Con Claude Code
```
/analizar-csv nombre_archivo.csv
```

### Con Python
```bash
python scripts/main.py analizar nombre_archivo.csv
```

### Que se analiza
- Campos vacios en columnas obligatorias
- Espacios al inicio/fin de valores
- Longitud de campos
- Caracteres invalidos o de control
- Formatos de fecha
- Validacion de RUTs
- Formatos de email

## 3. Validacion Especifica

### Configurar reglas
Editar `config/campos_rce.json` para definir:
- Campos obligatorios por tabla
- Longitudes maximas
- Valores permitidos (enums)
- Patrones regex

### Ejecutar validacion
```
/validar-campos nombre_archivo.csv
```

## 4. Generacion de Reportes

### Para TICS
```
/generar-reporte-tics
```

Genera:
- `output/listados_tics/{nombre}_revision_{fecha}.csv`
- `output/listados_tics/{nombre}_resumen_{fecha}.txt`

### Para DBA
```bash
python scripts/main.py sql nombre_archivo.csv --tabla nombre_tabla
```

Genera:
- `output/correcciones_tabla/{tabla}_correcciones_{fecha}.sql`

## 5. Entrega a TICS

### Archivos a entregar
1. **CSV de revision** - Lista completa de errores
2. **Resumen ejecutivo** - Para supervision
3. **Script SQL** - Para correcciones automatizables

### Formato del CSV de revision

| Columna | Descripcion |
|---------|-------------|
| fila | Numero de fila en archivo original |
| campo | Nombre del campo con error |
| valor_actual | Valor que tiene actualmente |
| tipo_error | Codigo del tipo de error |
| mensaje | Descripcion del error |
| accion_sugerida | Que hacer para corregir |
| prioridad | ALTA, MEDIA, BAJA |

## 6. Seguimiento

### Despues de correcciones
1. Solicitar nueva exportacion
2. Re-analizar para verificar
3. Comparar con anterior:
   ```
   /comparar-csv archivo_antes.csv archivo_despues.csv
   ```

### Registro
- Logs en `logs/analisis/`
- Mantener historico de analisis

## Diagrama de Flujo

```
     ┌──────────────────┐
     │ Recibir CSV RCE  │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ Colocar en       │
     │ csv_entrada/     │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ /analizar-csv    │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ Revisar errores  │
     │ en logs/         │
     └────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────┐       ┌─────────────┐
│Sin errs │       │ Con errores │
└────┬────┘       └──────┬──────┘
     │                   │
     │                   ▼
     │           ┌──────────────────┐
     │           │/generar-reporte- │
     │           │      tics        │
     │           └────────┬─────────┘
     │                    │
     │                    ▼
     │           ┌──────────────────┐
     │           │ Entregar a TICS: │
     │           │ - CSV revision   │
     │           │ - Resumen        │
     │           │ - Script SQL     │
     │           └────────┬─────────┘
     │                    │
     │                    ▼
     │           ┌──────────────────┐
     │           │ TICS corrige     │
     │           └────────┬─────────┘
     │                    │
     │                    ▼
     │           ┌──────────────────┐
     │           │ Nueva exportacion│
     │◄──────────┤ para verificar   │
     │           └──────────────────┘
     │
     ▼
┌──────────────────┐
│ Mover CSV a      │
│ csv_procesados/  │
└──────────────────┘
```

## Prioridades de Correccion

| Prioridad | Tipos de Error | Accion |
|-----------|----------------|--------|
| ALTA | CAMPO_VACIO, VALOR_INVALIDO | Correccion inmediata |
| MEDIA | FORMATO_FECHA, LONGITUD_EXCEDIDA | Planificar correccion |
| BAJA | ESPACIOS_EXTRA | Script automatico |
