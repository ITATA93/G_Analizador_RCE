# Reporte de Errores - Analisis RCE

**Archivo analizado:** {{archivo}}
**Fecha de analisis:** {{fecha}}
**Generado por:** Analizador RCE v1.0

---

## Resumen Ejecutivo

| Metrica | Valor |
|---------|-------|
| Total registros | {{total_filas}} |
| Registros con errores | {{filas_con_error}} |
| Tasa de error | {{tasa_error}}% |

---

## Errores por Tipo

| Tipo de Error | Cantidad | Porcentaje |
|---------------|----------|------------|
{{#errores_por_tipo}}
| {{tipo}} | {{cantidad}} | {{porcentaje}}% |
{{/errores_por_tipo}}

---

## Errores por Campo

| Campo | Cantidad | Accion Sugerida |
|-------|----------|-----------------|
{{#errores_por_campo}}
| {{campo}} | {{cantidad}} | {{accion}} |
{{/errores_por_campo}}

---

## Detalle de Errores (Primeros 100)

| Fila | Campo | Valor | Error | Accion |
|------|-------|-------|-------|--------|
{{#errores_detalle}}
| {{fila}} | {{campo}} | {{valor}} | {{error}} | {{accion}} |
{{/errores_detalle}}

---

## Proximos Pasos

1. [ ] Revisar errores de prioridad ALTA
2. [ ] Ejecutar scripts de correccion SQL
3. [ ] Coordinar con TICS para correcciones manuales
4. [ ] Re-analizar despues de correcciones

---

*Generado automaticamente - No editar manualmente*
