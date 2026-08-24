# ═══════════════════════════════════════════════════════════════════════
# DIAGNÓSTICO COMPLETO — Módulo Académico (Grupo / Periodo)
# Se ejecuta DENTRO de Django (usa el ORM real, no adivina tablas/columnas)
# No lo corras directo con python — usa el .ps1 que viene junto a este
# archivo, o manualmente:
#     Get-Content diagnostico_completo.py | python manage.py shell
# ═══════════════════════════════════════════════════════════════════════

import sys
from django.db.models import Count

print("=" * 90)
print("DIAGNÓSTICO COMPLETO — Módulo Académico (Grupo / Periodo)")
print("=" * 90)

try:
    from academic.models import Grupo, Periodo, Carrera
except ImportError as e:
    print(f"❌ No se pudo importar los modelos (¿el app se llama 'academic'?): {e}")
    sys.exit(1)

# ───────────────────────────────────────────────────────────────────────
# 0. ¿Existe el campo Periodo.tipo? ¿Grupo.nombre ya es opcional?
# ───────────────────────────────────────────────────────────────────────
print("\n--- 0. Campos esperados en el modelo ---")

tiene_tipo = 'tipo' in [f.name for f in Periodo._meta.get_fields()]
print(f"{'✅' if tiene_tipo else '❌'} Periodo.tipo {'existe' if tiene_tipo else 'NO existe — falta agregar y migrar'}")

campo_nombre = Grupo._meta.get_field('nombre')
print(f"{'✅' if campo_nombre.blank else '❌'} Grupo.nombre blank={campo_nombre.blank} "
      f"({'ya es autogenerado/opcional' if campo_nombre.blank else 'todavía requerido — falta migrar'})")

# ───────────────────────────────────────────────────────────────────────
# 1. UniqueConstraints — definidos en el código Y aplicados en BD
# ───────────────────────────────────────────────────────────────────────
print("\n--- 1. UniqueConstraints de identidad de Grupo ---")

esperados = ['unique_grupo_general_sin_especialidad', 'unique_grupo_por_especialidad']
nombres_constraints_codigo = [c.name for c in Grupo._meta.constraints]

for nombre in esperados:
    estado = '✅' if nombre in nombres_constraints_codigo else '❌'
    print(f"{estado} {nombre} — definido en Meta.constraints (código)")

from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(
        "SELECT conname FROM pg_constraint WHERE conrelid = %s::regclass AND contype = 'u'",
        [Grupo._meta.db_table],
    )
    constraints_bd = [row[0] for row in cursor.fetchall()]

print(f"\nConstraints UNIQUE encontrados en la BD para {Grupo._meta.db_table}: {constraints_bd or '(ninguno)'}")
for nombre in esperados:
    estado = '✅' if nombre in constraints_bd else '❌'
    print(f"{estado} {nombre} — aplicado en BD (migrado)")

# ───────────────────────────────────────────────────────────────────────
# 2. Duplicados por identidad real (grado + especialidad)
# ───────────────────────────────────────────────────────────────────────
print("\n--- 2. Grupos duplicados por identidad (plantel+periodo+carrera+grado+especialidad) ---")

dups = (
    Grupo.objects
    .values('plantel_id', 'periodo_id', 'carrera_id', 'grado', 'especialidad')
    .annotate(total=Count('id'))
    .filter(total__gt=1)
)
dups = list(dups)

if dups:
    for d in dups:
        ids = list(Grupo.objects.filter(
            plantel_id=d['plantel_id'], periodo_id=d['periodo_id'],
            carrera_id=d['carrera_id'], grado=d['grado'], especialidad=d['especialidad'],
        ).values_list('id', flat=True))
        print(f"❌ plantel={d['plantel_id']} periodo={d['periodo_id']} carrera={d['carrera_id']} "
              f"grado={d['grado']} especialidad={d['especialidad']} → {d['total']} grupos, ids={ids}")
else:
    print("✅ Sin duplicados de identidad")

# ───────────────────────────────────────────────────────────────────────
# 3. Grupos sin periodo asignado (bug original de "grupos huérfanos")
# ───────────────────────────────────────────────────────────────────────
print("\n--- 3. Grupos sin periodo asignado ---")

huerfanos = list(Grupo.objects.filter(periodo__isnull=True).select_related('carrera'))
if huerfanos:
    for g in huerfanos:
        try:
            n_alumnos = g.alumnos.count()
        except Exception:
            n_alumnos = '?'
        print(f"❌ id={g.id} | {g.carrera} | grado={g.grado} | alumnos={n_alumnos}")
else:
    print("✅ Todos los grupos tienen periodo asignado")

# ───────────────────────────────────────────────────────────────────────
# 4. Especialidad mal capturada
# ───────────────────────────────────────────────────────────────────────
print("\n--- 4. Grupos con especialidad mal capturada ---")

problemas = []
for g in Grupo.objects.select_related('carrera').all():
    es_prepa_avanzada = g.carrera and g.carrera.nivel == 'PREPARATORIA' and g.grado >= 5
    if es_prepa_avanzada and not g.especialidad:
        problemas.append((g, 'FALTA especialidad (grado >= 5 en Prepa)'))
    elif not es_prepa_avanzada and g.especialidad:
        problemas.append((g, 'SOBRA especialidad (no debería tenerla)'))

if problemas:
    for g, motivo in problemas:
        print(f"❌ id={g.id} | grado={g.grado} | especialidad={g.especialidad} | {motivo}")
else:
    print("✅ Sin inconsistencias de especialidad")

# ───────────────────────────────────────────────────────────────────────
# 5. Consistencia grado (par/impar) vs Periodo.tipo (NON/PAR)
# ───────────────────────────────────────────────────────────────────────
print("\n--- 5. Consistencia grado (non/par) vs Periodo.tipo ---")

if tiene_tipo:
    inconsistentes = []
    qs = (
        Grupo.objects
        .select_related('carrera', 'periodo')
        .filter(carrera__nivel='PREPARATORIA', periodo__activo=True)
    )
    for g in qs:
        tipo_esperado = 'NON' if g.grado % 2 == 1 else 'PAR'
        if not g.periodo or not g.periodo.tipo:
            inconsistentes.append((g, 'periodo sin tipo asignado'))
        elif g.periodo.tipo != tipo_esperado:
            inconsistentes.append((g, f'esperado={tipo_esperado}, real={g.periodo.tipo}'))

    if inconsistentes:
        for g, motivo in inconsistentes:
            print(f"❌ id={g.id} | grado={g.grado} | periodo={g.periodo} | {motivo}")
    else:
        print("✅ Todos los grupos de Prepa activos coinciden con el tipo de su periodo")
else:
    print("⏭️  Se omite — Periodo.tipo no existe todavía (ver punto 0)")

# ───────────────────────────────────────────────────────────────────────
# 6. Planteles con más de 1 periodo activo (rompe el supuesto base)
# ───────────────────────────────────────────────────────────────────────
print("\n--- 6. Planteles con más de 1 periodo activo ---")

dup_periodos = list(
    Periodo.objects.filter(activo=True)
    .values('plantel_id').annotate(total=Count('id')).filter(total__gt=1)
)
if dup_periodos:
    for d in dup_periodos:
        print(f"❌ plantel_id={d['plantel_id']} tiene {d['total']} periodos activos")
else:
    print("✅ Cada plantel tiene máximo 1 periodo activo")

# ───────────────────────────────────────────────────────────────────────
# RESUMEN
# ───────────────────────────────────────────────────────────────────────
print("\n" + "=" * 90)
print("RESUMEN")
print("=" * 90)
print(f"Periodo.tipo existe:                {'SÍ' if tiene_tipo else 'NO'}")
print(f"Grupo.nombre autogenerado (blank):  {'SÍ' if campo_nombre.blank else 'NO'}")
print(f"Constraints en código:              {sum(1 for n in esperados if n in nombres_constraints_codigo)}/2")
print(f"Constraints aplicados en BD:        {sum(1 for n in esperados if n in constraints_bd)}/2")
print(f"Grupos duplicados encontrados:      {len(dups)}")
print(f"Grupos sin periodo:                 {len(huerfanos)}")
print(f"Grupos con especialidad mal:        {len(problemas)}")
print(f"Planteles con >1 periodo activo:    {len(dup_periodos)}")
print("=" * 90)

todo_bien = (
    tiene_tipo and campo_nombre.blank
    and len(constraints_bd) == 2
    and not dups and not huerfanos and not problemas and not dup_periodos
)
if todo_bien:
    print("🎉 TODO EN ORDEN — no se detectaron pendientes")
else:
    print("⚠️  HAY PENDIENTES — revisa los ❌ arriba")