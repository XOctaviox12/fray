"""
Script de datos de prueba para FRAY.
Uso: python manage.py shell -c "exec(open('seed_demo.py').read())"
"""

import random
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta, date

from campuses.models import Plantel
from users.models import User, DocenteGrupo
from academic.models import (
    Periodo, Carrera, Grupo, Asignatura,
    Tarea, EntregaTarea, Actividad, EntregaActividad,
    Calificacion,
)

print("Iniciando seed de datos de prueba...")

# 1. Plantel
plantel, _ = Plantel.objects.get_or_create(
    nombre='Plantel Demo',
    defaults={'direccion': 'Av. Principal 123', 'nivel_educativo': 'SUPERIOR'}
)
print(f"Plantel: {plantel}")

# 2. Periodo
periodo, _ = Periodo.objects.get_or_create(
    nombre='Ene-Abr 2026',
    defaults={
        'fecha_inicio': date(2026, 1, 1),
        'fecha_fin':    date(2026, 4, 30),
        'activo':       True,
    }
)
print(f"Periodo: {periodo}")

# 3. Carrera
carrera, _ = Carrera.objects.get_or_create(
    nombre='Ingeniería en Sistemas',
    plantel=plantel,
    defaults={'nivel': 'UNIVERSIDAD'}
)
print(f"Carrera: {carrera}")

# 4. Asignaturas
materias_data = ['Matemáticas', 'Programación', 'Base de Datos']
asignaturas = []
for nombre in materias_data:
    asig, _ = Asignatura.objects.get_or_create(
        nombre=nombre,
        carrera=carrera,
        defaults={'clave': nombre[:3].upper(), 'creditos': 5}
    )
    asignaturas.append(asig)
print(f"Asignaturas: {[a.nombre for a in asignaturas]}")

# 5. Docente
docente, created = User.objects.get_or_create(
    username='docente_demo',
    defaults={
        'first_name': 'Juan Carlos',
        'last_name':  'Ponce',
        'email':      'docente@demo.com',
        'rol':        'DOCENTE',
        'plantel':    plantel,
        'estatus':    'ACTIVO',
    }
)
if created:
    docente.set_password('demo1234')
    docente.save()
print(f"Docente: {docente} ({'creado' if created else 'ya existia'})")

# 6. Grupos
grupos = []
for nombre in ['A', 'B']:
    grupo, _ = Grupo.objects.get_or_create(
        nombre=nombre,
        plantel=plantel,
        carrera=carrera,
        defaults={
            'grado':            1,
            'periodo':          periodo,
            'capacidad_maxima': 15,
        }
    )
    grupo.docentes.add(docente)
    grupos.append(grupo)
print(f"Grupos: {[str(g) for g in grupos]}")

# Asignar asignaturas a grupos
for grupo in grupos:
    for asig in asignaturas:
        grupo.asignaturas.add(asig)
        asig.docentes.add(docente)

# 7. DocenteGrupo
for grupo in grupos:
    for asig in asignaturas:
        DocenteGrupo.objects.get_or_create(
            docente=docente,
            grupo=grupo,
            asignatura=asig,
            defaults={'ciclo': '2026-1', 'activo': True}
        )
print("Asignaciones DocenteGrupo creadas")

# 8. Alumnos
nombres = [
    ('Ana', 'Garcia'), ('Luis', 'Martinez'), ('Maria', 'Lopez'),
    ('Carlos', 'Hernandez'), ('Sofia', 'Ramirez'), ('Diego', 'Torres'),
    ('Valeria', 'Flores'), ('Andres', 'Morales'), ('Daniela', 'Jimenez'),
    ('Roberto', 'Reyes'),
]

alumnos_por_grupo = {}
for grupo in grupos:
    alumnos = []
    for i, (nombre, apellido) in enumerate(nombres):
        username = f"alumno_{grupo.nombre.lower()}_{i+1}"
        alumno, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name':   nombre,
                'last_name':    apellido,
                'email':        f"{username}@demo.com",
                'rol':          'ALUMNO',
                'plantel':      plantel,
                'alumno_grupo': grupo,
                'estatus':      'ACTIVO',
            }
        )
        if not created:
            alumno.alumno_grupo = grupo
            alumno.save()
        if created:
            alumno.set_password('demo1234')
            alumno.save()
        alumnos.append(alumno)
    alumnos_por_grupo[grupo.pk] = alumnos
print(f"Alumnos creados: {sum(len(v) for v in alumnos_por_grupo.values())}")

# 9. Tareas + Entregas
ahora = timezone.now()
tareas_creadas = 0
entregas_creadas = 0

for grupo in grupos:
    alumnos = alumnos_por_grupo[grupo.pk]
    for asig in asignaturas:
        for t in range(1, 4):
            fecha_entrega = ahora - timedelta(days=random.randint(5, 30))
            tarea, _ = Tarea.objects.get_or_create(
                titulo=f"Tarea {t} - {asig.nombre}",
                grupo=grupo,
                asignatura=asig,
                docente=docente,
                defaults={
                    'descripcion':   f'Descripcion de la tarea {t} de {asig.nombre}',
                    'fecha_entrega': fecha_entrega,
                    'publicada':     True,
                    'activa':        True,
                }
            )
            tareas_creadas += 1
            for alumno in alumnos[:8]:
                nota = Decimal(str(round(random.uniform(5.0, 10.0), 1)))
                EntregaTarea.objects.get_or_create(
                    tarea=tarea,
                    alumno=alumno,
                    defaults={
                        'comentario':    'Entrega de prueba',
                        'estado':        'CALIFICADA',
                        'calificacion':  nota,
                        'feedback':      'Buen trabajo.',
                        'calificada_en': ahora,
                    }
                )
                entregas_creadas += 1

print(f"Tareas: {tareas_creadas} | Entregas: {entregas_creadas}")

# 10. Actividades + Entregas
actividades_creadas = 0
entregas_act_creadas = 0

for grupo in grupos:
    alumnos = alumnos_por_grupo[grupo.pk]
    for asig in asignaturas:
        for a in range(1, 4):
            fecha_entrega = ahora - timedelta(days=random.randint(3, 20))
            actividad, _ = Actividad.objects.get_or_create(
                titulo=f"Actividad {a} - {asig.nombre}",
                grupo=grupo,
                asignatura=asig,
                docente=docente,
                defaults={
                    'instrucciones': f'Instrucciones de la actividad {a}',
                    'tipo':          'ABIERTA',
                    'fecha_entrega': fecha_entrega,
                    'publicada':     True,
                    'valor_total':   Decimal('10.00'),
                }
            )
            actividades_creadas += 1
            for alumno in alumnos[:7]:
                nota = Decimal(str(round(random.uniform(6.0, 10.0), 1)))
                EntregaActividad.objects.get_or_create(
                    actividad=actividad,
                    alumno=alumno,
                    defaults={
                        'calificacion': nota,
                        'feedback':     'Actividad completada.',
                    }
                )
                entregas_act_creadas += 1

print(f"Actividades: {actividades_creadas} | Entregas: {entregas_act_creadas}")

# 11. Calificaciones manuales
cals_creadas = 0
for grupo in grupos:
    alumnos = alumnos_por_grupo[grupo.pk]
    for asig in asignaturas:
        for alumno in alumnos:
            nota = Decimal(str(round(random.uniform(6.5, 10.0), 1)))
            Calificacion.objects.get_or_create(
                alumno=alumno,
                asignatura=asig,
                grupo=grupo,
                tipo='MANUAL',
                defaults={'nota': nota, 'docente': docente}
            )
            cals_creadas += 1

print(f"Calificaciones manuales: {cals_creadas}")
print("\nSeed completado!")
print("  Docente: docente_demo / demo1234")
print(f"  Grupos: {[str(g) for g in grupos]}")
print("  Alumnos por grupo: 10")