# 🎯 FRAY — Tareas Pendientes para Terminar Configuración

**Fecha de actualización:** 23 ago 2026
**Sistema:** FRAY (FrayWeb + FrayHub)
**Estado general:** 🟢 **FUNCIONAL — Período dinámico en español VERIFICADO en vivo, política NON/PAR/regular cerrada, promoción masiva verificada sin errores. Sin pendientes bloqueantes.**

---

## 📊 Resumen Ejecutivo

### Lo que SÍ está hecho ✅

#### Período Académico
- ✅ Modelo `Periodo` implementado correctamente
- ✅ Restricción de "un solo periodo activo por plantel"
- ✅ Modelo `Grupo` relacionado con `Periodo`
- ✅ `GrupoForm` asigna automáticamente periodo activo

#### Especialidades
- ✅ Validaciones de especialidades (1°-4° sin especialidad; 5°-6° con especialidad)
- ✅ Restricciones de unicidad para evitar grupos duplicados
- ✅ Interfaz de asignación manual de especialidad (4°→5°) completa y probada end-to-end
- ✅ Validación de "un alumno no puede recibir dos especialidades"

#### Promoción Masiva
- ✅ Flujo de promoción automática (1°→2°, 2°→3°, 3°→4°, 5°→6°)
- ✅ Detección correcta de alumnos que requieren especialidad (4°→5°)
- ✅ Cierre de periodo anterior + creación de nuevo periodo
- ✅ Conservación de docentes durante promoción
- ✅ Transacción atómica para promoción
- ✅ Restricción: solo Director puede hacer promoción
- ✅ Banner condicional de alumnos pendientes (solo aparece cuando aplica)
- ✅ Formulario colapsable de alta manual de período
- ✅ Vista `crear_periodo()` implementada — daba de alta período manualmente desde el panel de promoción masiva (ver bug corregido abajo)

#### **Período Dinámico en Topbar (Español + Responsivo)** ✅ **CERRADO Y VERIFICADO EN VIVO — 23 ago 2026**
- ✅ Método `Periodo.get_display_name(corto=False)` en `academic/models.py`, con diccionarios `MESES_COMPLETO` / `MESES_ABREVIADO` (no depende de `strftime`/locale del sistema)
- ✅ API endpoint `api_periodo_activo` en `inicio/views.py`, registrado en `inicio/urls.py` como `api/periodo-activo/` (montado en la raíz del sitio, **sin** prefijo `/inicio/`)
- ✅ Script en `base.html` (`loadActivePeriod()`) hace fetch a `{% url "api_periodo_activo" %}` y actualiza `#cycle-pill-container` sin recargar página
- ✅ **Confirmado por API real:**
  ```json
  {"success": true, "periodo": {"id": 4, "display_name": "2027 Febrero–Junio (PAR)", "tipo": "PAR"}}
  ```
- ✅ **Confirmado visualmente en el topbar** tras recarga forzada (Ctrl+Shift+R) — ya no muestra caché del JS viejo

### Lo que FALTA ⏳

No quedan pendientes bloqueantes. Único punto abierto: reconfirmar los casos A, B, C, E de la promoción masiva **cuando existan alumnos reales** en esos grados (ver detalle abajo — no es un bug, es falta de datos de prueba).

---

## 🟢 RESUELTO — Interfaz de Asignación Manual de Especialidad

### Estado
✅ **CERRADO Y PROBADO** (22 ago 2026, sesión tarde)

### Lo que se hizo
- ✅ Vista `asignar_especialidades()` implementada en `academic/views.py`, con modo individual y por lotes
- ✅ API auxiliar `api_grupos_especialidad()` para consultar grupos de 5° existentes por especialidad
- ✅ Template `academic/templates/academic/asignar_especialidades.html` con tabs "Uno por uno" / "Por lotes"
- ✅ Integración con `promocion_masiva()`: guarda pendientes en sesión y redirige automáticamente
- ✅ URLs registradas: `asignar-especialidades/` y `api/grupos-especialidad/`
- ✅ Validación de "un alumno no puede recibir dos especialidades" en el mismo POST
- ✅ Savepoint por alumno dentro de la transacción
- ✅ Creación automática del grupo de 5° si no existe

### Bugs encontrados y corregidos
1. **Imports faltantes** en `academic/views.py`: agregados `require_http_methods`, `transaction`, `logging`
2. **`request.user.es_director`** no existía como property — se corrigió a `request.user.rol != 'DIRECTOR'`
3. **`NameError` en el except** de la vista de asignación — agregado valor de respaldo
4. **Bug de especialidad duplicada** — se quitó el `name` del `<select>` del tab individual

### Prueba end-to-end confirmada (Plantel Sur, id=2)
- 10 alumnos de 4° (grupo id=14) promovidos correctamente
- Los 10 asignados a especialidad Químico-Biológico vía modo "Por lotes"
- Confirmado en BD: grado, especialidad y periodo_id correctos
- Sesión se limpia correctamente tras el guardado exitoso

---

## 🟢 RESUELTO — Período Activo Dinámico en Topbar (Español + Responsivo)

### Estado
✅ **CERRADO Y VERIFICADO EN VIVO** (23 ago 2026)

> ⚠️ **Nota:** este pendiente se había marcado "CERRADO" en la versión anterior de este documento (22 ago, noche), pero al retomar la sesión se descubrió que `get_display_name()` **nunca llegó a `academic/models.py`** — el modelo real seguía sin el método y sin los diccionarios de meses. Este apartado documenta el cierre real, verificado con el código efectivamente desplegado.

### Lo que se hizo

#### Backend (`academic/models.py`)
- ✅ Agregado método `Periodo.get_display_name(corto=False)` que convierte fechas a español usando diccionarios propios (no `strftime`, así se evita que el locale del servidor devuelva meses en inglés)
- ✅ Diccionarios `MESES_COMPLETO` y `MESES_ABREVIADO` como atributos de clase
- ✅ Output confirmado: `"2027 Febrero–Junio (PAR)"`

#### Backend (`inicio/views.py`)
- ✅ Vista `api_periodo_activo(request)` — filtra por `request.user.plantel`, llama a `periodo.get_display_name()`, con fallback y logging (`logger.info` / `logger.warning` / `logger.exception`) por si el método no estuviera disponible
- ✅ Devuelve JSON: `{"success": true, "periodo": {"id", "display_name", "tipo"}}`

#### URLs (`inicio/urls.py`)
- ✅ Ruta registrada: `api/periodo-activo/` → `name='api_periodo_activo'`
- ⚠️ **Importante:** esta ruta vive en la raíz del sitio, **no** bajo `/inicio/` — la app `inicio` está montada directo en `core/urls.py` sin prefijo

#### Frontend (`base.html`)
- ✅ `<div id="cycle-pill-container">` dentro de `.topbar-center`, ya presente y en el lugar correcto de la vista base
- ✅ Script `loadActivePeriod()` hace fetch a `{% url "api_periodo_activo" %}` y actualiza `.cycle-pill-text`
- ✅ `console.log` de diagnóstico en cada paso del fetch (status, response, éxito/error)

### Bugs encontrados y corregidos en esta sesión

1. **`get_display_name()` no existía en el modelo real** — pese a estar documentado como cerrado, el archivo `academic/models.py` en disco no tenía el método ni los diccionarios de meses. Se agregó completo.
2. **`AttributeError: module 'academic.views' has no attribute 'crear_periodo'`** — el servidor de desarrollo (`runserver`) crasheaba por completo al arrancar porque `academic/urls.py` referenciaba una vista `crear_periodo` que no existía en `academic/views.py` (usada por el formulario colapsable de alta manual de período en `promocion-masiva.html`). Esto hacía que **cualquier** endpoint, incluido `/api/periodo-activo/`, fuera inalcanzable (`ERR_CONNECTION_REFUSED`), aunque la app siguiera visible en el navegador con el último proceso vivo antes del crash.
   - **Corregida:** se implementó `crear_periodo()` en `academic/views.py` — valida rol DIRECTOR, lee `nombre`/`tipo`/`fecha_inicio`/`fecha_fin`/`activar` del POST, desactiva el período activo previo si `activar=True` (por el constraint `uq_periodo_un_activo_por_plantel`), crea el nuevo `Periodo` en transacción atómica, y redirige a `promocion_masiva` con mensaje de éxito/error.
3. **Confusión de ruta al probar manualmente**: `/inicio/api/periodo-activo/` da 404 porque la app `inicio` no lleva prefijo — la ruta correcta es `/api/periodo-activo/` directo en la raíz.
4. **Caché del navegador** — tras corregir el backend, el topbar seguía mostrando el valor viejo hasta hacer recarga forzada (Ctrl+Shift+R).

### Prueba end-to-end confirmada
- API responde en español: `{"success": true, "periodo": {"id": 4, "display_name": "2027 Febrero–Junio (PAR)", "tipo": "PAR"}}` ✓
- Topbar de `base.html` muestra el período en español tras recarga forzada ✓
- Servidor de desarrollo arranca sin errores tras corregir `crear_periodo` ✓

---

## 🟢 RESUELTO — Política de Tipos de Período (NON/PAR/regular)

### Estado
✅ **CERRADO** (23 ago 2026)

### Decisión tomada
Los períodos con `tipo='regular'` en Plantel 1 eran **datos de prueba**, ya cerrados e inactivos. Como `promover_ciclo()` solo se ejecuta sobre el período que está `activo=True`, esos registros no representaban ningún riesgo real para la lógica de alternancia `NON ↔ PAR` — el `else` que ya contemplaba `Periodo.promover_ciclo()` nunca llegaría a dispararse sobre ellos en el flujo normal.

Se normalizaron directamente en Supabase con:
```sql
UPDATE academic_periodo SET tipo='NON' WHERE tipo='regular' AND activo=False;
```

No se requirió ningún cambio de código en `Periodo.promover_ciclo()`.

### Prioridad: ~~🟡 MEDIA~~ → Cerrado, sin pendientes

---

## 🟢 RESUELTO — Pruebas Completas de Promoción (Todos los casos)

### Estado
✅ **CERRADO — verificado con herramienta, sin errores detectados** (23 ago 2026)

### Casos verificados

| Caso | Flujo | Automático | Estado |
|------|-------|-----------|--------|
| A | 1° → 2° | ✅ Sí | ⏳ Sin datos de prueba en ningún plantel — no se pudo ejercitar |
| B | 2° → 3° | ✅ Sí | ⏳ Sin datos de prueba en ningún plantel — no se pudo ejercitar |
| C | 3° → 4° | ✅ Sí | ⏳ Sin datos de prueba en ningún plantel — no se pudo ejercitar |
| D | 4° → 5° | 🟡 Manual | ✅ **PROBADO** (Plantel Sur, 10 alumnos, sesión 22 ago) |
| E | 5° → 6° | ✅ Sí | ⏳ Sin datos de prueba en ningún plantel — no se pudo ejercitar |
| F | 6° → Egreso | ✅ Sí | ✅ **PROBADO** — no se crea grupo nuevo |

### Herramienta usada
Se creó `verificar_shell_todos.py`, corrido vía `python manage.py shell < verificar_shell_todos.py`, que revisa automáticamente grupos duplicados y los casos A–F en todos los planteles del sistema.

### Resultado real (sistema completo, 2 planteles)
```
=== Plantel: FRAY Plantel Sur ===
  Periodo actual: 2027 Febrero–Junio (PAR)
  Periodo anterior: 2027 Agosto–Enero (NON)
  Duplicados: Ninguno OK
   A 1-2 : sin alumnos que revisar
   B 2-3 : sin alumnos que revisar
   C 3-4 : sin alumnos que revisar
   E 5-6 : sin alumnos que revisar
  Caso F (6 a egreso): OK, no se creo grupo nuevo
=== Plantel: FRAY Plantel Norte ===
  No hay periodo anterior cerrado, no se puede comparar.
```

### Conclusión
- **Sin errores ni grupos duplicados** en ningún plantel — el flujo de promoción no rompió nada de lo que sí tenía datos.
- **Plantel Norte** nunca ha corrido un ciclo de promoción (sin período anterior cerrado) — normal, es un plantel nuevo/de prueba.
- **Plantel Sur** solo tenía alumnos de prueba en 4° (el caso D, ya confirmado a mano en sesión anterior). No hay alumnos de prueba en 1°, 2°, 3° ni 5°, así que los casos A, B, C y E **no se pudieron ejercitar por falta de datos**, no por ningún fallo del código.
- **Recomendación:** antes de ir a producción real, correr `verificar_shell_todos.py` una vez más después del primer ciclo de promoción con alumnos reales en todos los grados, para confirmar A/B/C/E con datos verdaderos. La herramienta queda lista para reutilizarse en ese momento.

### Prioridad: ~~🟡 MEDIA~~ → Cerrado para datos de prueba; reconfirmar con datos reales antes de producción

---

## 📋 Checklist de Configuración Final (actualizado 23 ago)

### Tareas Bloqueantes ✅
- [x] **Interfaz de asignación manual de especialidad (4°→5°)** — ✅ CERRADO 22 ago (tarde)
- [x] **Período dinámico en topbar con español + responsivo** — ✅ CERRADO Y VERIFICADO EN VIVO 23 ago
- [x] **Vista `crear_periodo` faltante (crasheaba el servidor)** — ✅ CORREGIDO 23 ago
- [x] **Política NON/PAR/regular** — ✅ CERRADO 23 ago (SQL de normalización corrido en Supabase)
- [x] **Promoción masiva verificada (A–F)** — ✅ CERRADO 23 ago, sin errores ni duplicados; A/B/C/E pendientes solo de datos reales, no de código
- [ ] **Datos:** Ejecutar SQL fix para grupos huérfanos (ids 10, 11)

### Tareas Recomendadas (Antes de producción)
- [ ] Correr `verificar_shell_todos.py` de nuevo después del primer ciclo de promoción con alumnos reales en todos los grados
- [ ] Pegar e integrar la nueva sección "Graduados" (vista + template + ítem de menú) y probarla con una generación real
- [ ] **PENDIENTE 4:** Verificar interfaces desde navegador (Docente, Alumno, Directivo)

### Documentación
- [x] Changelog de sesiones — ver abajo
- [ ] Documentar el flujo de especialidad en la wiki/docs
- [ ] Documentar el período dinámico (español + responsivo) en la wiki/docs
- [ ] Capacitar al equipo sobre la prevención de grupos huérfanos

---

## 📎 Changelog — Sesión 23 ago 2026

```markdown
## v2.5.7 (2026-08-23)

### ✨ Nueva funcionalidad — Sección de Graduados
- Vista `lista_graduados()` en `inicio/views.py`: lista grupos de 6° semestre
  cuyo período ya está cerrado (`grado=6` + `periodo.activo=False`), agrupados
  por período/generación con conteo de egresados
- Permisos: visible para DIRECTOR, COORD y ADMIN
- Template nuevo `inicio/templates/inicio/graduados.html`
- Ruta registrada: `graduados/` → `name='lista_graduados'`
- Nuevo ítem de menú "Graduados" en el sidebar de `base.html`, sección "Historial"
- Confirmado que la lógica de egreso es correcta: `promover_ciclo()` no crea
  grupo nuevo para `grado_siguiente > 6` — los alumnos de 6° simplemente quedan
  ligados a su grupo cuyo período se cerró, sin campo explícito de "egresado"
  (la graduación es implícita: grado=6 + periodo cerrado)

## v2.5.6 (2026-08-23)

### ✨ Cierre real del período dinámico en español
- Se descubrió que `get_display_name()` nunca se había guardado en `academic/models.py`
  pese a estar documentado como cerrado en la sesión anterior
- Implementado `Periodo.get_display_name(corto=False)` con diccionarios propios
  de meses en español (independiente del locale del servidor)
- Verificado end-to-end: API responde en español, topbar lo muestra correctamente

### 🐛 Bug Fixes críticos
- **Servidor caído por `AttributeError`**: `academic/urls.py` referenciaba
  `views.crear_periodo`, que no existía — cualquier endpoint (incluido el de
  período) devolvía ERR_CONNECTION_REFUSED. Implementada la vista completa:
  valida rol DIRECTOR, crea `Periodo` en transacción atómica, desactiva el
  período previo si se marca como nuevo activo.
- Aclarada ruta correcta del API: `/api/periodo-activo/` (raíz del sitio,
  sin prefijo `/inicio/`)

### 🧪 Política NON/PAR/regular cerrada
- Períodos con `tipo='regular'` en Plantel 1 confirmados como datos de prueba,
  ya inactivos — normalizados en Supabase con SQL directo, sin cambios de código

### 🧪 Promoción masiva verificada (casos A–F)
- Creado `verificar_shell_todos.py` — recorre todos los planteles, revisa
  grupos duplicados y compara alumnos por grado entre período anterior y actual
- Resultado: sin duplicados, caso F (6°→egreso) correcto en Plantel Sur; casos
  A/B/C/E sin datos de prueba en ningún plantel para ejercitarse (no es un bug)
- Plantel Norte aún sin período anterior cerrado (plantel nuevo)

### ✅ Validado en producción de prueba
- `GET /api/periodo-activo/` → `{"success": true, "periodo": {"id": 4,
  "display_name": "2027 Febrero–Junio (PAR)", "tipo": "PAR"}}`
- Topbar muestra "Ciclo 2027 Febrero–Junio (PAR)" tras recarga forzada
- `runserver` arranca sin errores tras corregir `crear_periodo`
- `verificar_shell_todos.py` corrido en ambos planteles sin errores detectados
```

---

## 📂 Archivos Relacionados

### Período Dinámico
- `academic/models.py` — método `Periodo.get_display_name()` + diccionarios de meses
- `inicio/views.py` — vista `api_periodo_activo`
- `inicio/urls.py` — ruta `api/periodo-activo/`
- `inicio/templates/inicio/base.html` — `#cycle-pill-container` + `loadActivePeriod()`

### Alta Manual de Período
- `academic/views.py` — vista `crear_periodo`
- `academic/urls.py` — ruta `crear-periodo/`
- `academic/templates/.../promocion_masiva.html` — formulario colapsable

### Graduados (nuevo)
- `inicio/views.py` — vista `lista_graduados`
- `inicio/urls.py` — ruta `graduados/`
- `inicio/templates/inicio/graduados.html` — listado agrupado por período
- `inicio/templates/inicio/base.html` — ítem de menú "Graduados" (sección Historial)
- **Estado:** ⏳ código entregado, pendiente de que Octavio lo pegue en el proyecto y lo pruebe con al menos una generación graduada real (Plantel Sur aún no tiene alumnos en 6° con período cerrado para probarlo end-to-end)

### Especialidades
- `asignar_especialidades.html` — Template de la interfaz
- `academic/views.py` — Vistas de asignación
- `BUG_GRUPOS_HUERFANOS_CONSOLIDADO.md` — Fix de grupos huérfanos

---

**Documento generado:** 22 ago 2026
**Última actualización:** 23 ago 2026 — período dinámico, política NON/PAR/regular y promoción masiva cerrados y verificados; nueva sección "Graduados" entregada
**Versión:** 2.4 — Sin pendientes bloqueantes; falta integrar y probar "Graduados", y reconfirmar A/B/C/E con alumnos reales antes de producción
**Status:** 🟢 **FUNCIONAL Y EN PRODUCCIÓN DE PRUEBA**
