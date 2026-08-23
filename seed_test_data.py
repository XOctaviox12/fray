"""
Carga datos de prueba COMPLETOS para Plantel 2:
  1) Promoción Masiva — grupos en TODOS los grados (1° a 6°) del ciclo activo
  2) Graduados + Historial Académico — un grupo de 6° en un ciclo YA CERRADO
  3) Calificaciones Parciales (BoletaParcial) — 4 parciales x múltiples materias
  4) Boleta Académica — historial completo de notas publicadas
  5) Reporte de Calificaciones — datos listos para generar reportes
  6) SesionClase + BloqueClase — sesiones en vivo de ejemplo

Uso:
    python manage.py shell < seed_test_data_mejorado.py

Es idempotente (usa get_or_create) — puedes correrlo varias veces sin
duplicar registros ni romper los unique_together.
"""

import datetime
import random
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from campuses.models import Plantel
from academic.models import (
    Periodo, Carrera, Grupo, Asignatura, BoletaParcial,
    SesionClase, BloqueClase
)
from users.models import User

# ── Cargar en Plantel 2 ──
planteles = Plantel.objects.all().order_by('id')
print(f"\n🏫 Planteles disponibles:")
for p in planteles:
    print(f"   - {p.id}: {p.nombre}")

plantel = Plantel.objects.filter(id=2).first()
if not plantel:
    print("\n❌ ERROR: No existe Plantel con id=2")
    print(f"   Usa un ID de plantel válido o crea uno primero.")
    exit(1)

print(f"\n✓ Usando plantel: {plantel} (ID={plantel.id})")

with transaction.atomic():

    # Crear carrera según nivel del plantel
    nivel_carrera = 'PREPARATORIA' if plantel.nivel_educativo == 'BASICA' else 'UNIVERSIDAD'
    nombre_carrera = 'Bachillerato General' if nivel_carrera == 'PREPARATORIA' else 'Licenciatura en Sistemas'
    
    carrera, _ = Carrera.objects.get_or_create(
        plantel=plantel, nombre=nombre_carrera, nivel=nivel_carrera,
        defaults={'clave_rvoe': f'TEST-{plantel.id:03d}'},
    )
    print(f"Carrera: {carrera.nombre} ({carrera.get_nivel_display()})")

    # ── Periodo activo (usa el que ya exista; si no hay, crea uno) ──
    periodo_activo = Periodo.objects.filter(plantel=plantel, activo=True).first()
    if not periodo_activo:
        periodo_activo = Periodo.objects.create(
            plantel=plantel, nombre='2026 Agosto–Enero TEST', tipo='NON',
            fecha_inicio=datetime.date(2026, 8, 1),
            fecha_fin=datetime.date(2027, 1, 31),
            activo=True,
        )
    print(f"Periodo activo: {periodo_activo}")

    # ── Periodo YA CERRADO, para simular una generación graduada ──
    periodo_cerrado, creado = Periodo.objects.get_or_create(
        plantel=plantel, nombre='2026 Febrero–Junio TEST',
        defaults={
            'tipo': 'PAR', 'activo': False,
            'fecha_inicio': datetime.date(2026, 2, 1),
            'fecha_fin': datetime.date(2026, 6, 30),
        },
    )
    print(f"Periodo cerrado (para graduados): {periodo_cerrado} (nuevo={creado})")

    docente, _ = User.objects.get_or_create(
        username='docente.test', plantel=plantel,
        defaults={'rol': 'DOCENTE', 'first_name': 'Docente', 'last_name': 'Prueba'},
    )
    if not docente.has_usable_password():
        docente.set_password('test1234')
        docente.set_password_recuperable('test1234')
        docente.save()

    # ══════════════════════════════════════════════════════════════
    # SETUP: Crear docentes adicionales (1 por materia)
    # ══════════════════════════════════════════════════════════════
    docentes_por_materia = {}
    for i, nombre_mat in enumerate(['Matemáticas', 'Historia', 'Química', 'Inglés', 'Español', 'Física'], 1):
        docente_mat, _ = User.objects.get_or_create(
            username=f'docente.{nombre_mat.lower()}.{i}', plantel=plantel,
            defaults={
                'rol': 'DOCENTE',
                'first_name': f'Prof. {nombre_mat}',
                'last_name': 'Prueba',
            },
        )
        if not docente_mat.has_usable_password():
            docente_mat.set_password('test1234')
            docente_mat.set_password_recuperable('test1234')
            docente_mat.save()
        docentes_por_materia[nombre_mat] = docente_mat
        print(f"Docente: {docente_mat.username}")

    # ══════════════════════════════════════════════════════════════
    # SETUP: Crear asignaturas por grado
    # ══════════════════════════════════════════════════════════════
    asignaturas_por_grado = {}
    materias_por_grado = {
        1: ['Matemáticas I', 'Historia de México', 'Química', 'Inglés I'],
        2: ['Matemáticas II', 'Historia Universal', 'Química II', 'Inglés II'],
        3: ['Matemáticas III', 'Historia Moderna', 'Física', 'Inglés III'],
        4: ['Matemáticas IV', 'Historia Contemporánea', 'Física II', 'Inglés IV'],
        5: ['Matemáticas V', 'Historia de América', 'Química III', 'Inglés V'],
        6: ['Matemáticas VI', 'Historia de México', 'Química', 'Inglés VI'],
    }
    for grado, materias in materias_por_grado.items():
        asignaturas_por_grado[grado] = []
        for nombre_mat in materias:
            materia_base = nombre_mat.split()[0]  # Extraer "Matemáticas", "Historia", etc.
            asig, _ = Asignatura.objects.get_or_create(
                carrera=carrera, nombre=nombre_mat,
                defaults={'clave': nombre_mat[:6].upper(), 'creditos': 5},
            )
            asignaturas_por_grado[grado].append(asig)
        print(f"Asignaturas grado {grado}: {len(asignaturas_por_grado[grado])} creadas/existentes")

    # ══════════════════════════════════════════════════════════════
    # 1) GRUPOS DEL CICLO ACTIVO (grados 1-6) — para Promoción Masiva
    # ══════════════════════════════════════════════════════════════
    grupos_activos = {}
    for grado in range(1, 7):
        grupo, _ = Grupo.objects.get_or_create(
            plantel=plantel, periodo=periodo_activo, carrera=carrera,
            grado=grado, especialidad=None,
            defaults={'aula': f'Aula {grado}', 'capacidad_maxima': 30},
        )
        grupos_activos[grado] = grupo
        print(f"Grupo activo grado {grado}: {grupo} (id={grupo.id})")

        # Agregar asignaturas al grupo (M2M)
        for asig in asignaturas_por_grado.get(grado, []):
            grupo.asignaturas.add(asig)
            # Asignar docente a la asignatura (M2M)
            materia_base = asig.nombre.split()[0]
            if materia_base in docentes_por_materia:
                asig.docentes.add(docentes_por_materia[materia_base])
        
        # También agregar los docentes al grupo (M2M)
        for asig in asignaturas_por_grado.get(grado, []):
            materia_base = asig.nombre.split()[0]
            if materia_base in docentes_por_materia:
                grupo.docentes.add(docentes_por_materia[materia_base])

    # Crear alumnos y asignarles calificaciones
    alumnos_por_grupo = {}
    for grado, grupo in grupos_activos.items():
        alumnos_por_grupo[grado] = []
        for i in range(1, 4):  # 3 alumnos por grado
            username = f'alumno.g{grado}.{i}'
            alumno, creado = User.objects.get_or_create(
                username=username, plantel=plantel,
                defaults={
                    'rol': 'ALUMNO',
                    'first_name': f'Alumno{grado}{i}',
                    'last_name': 'Prueba',
                    'alumno_grupo': grupo,
                },
            )
            if creado:
                alumno.set_password('test1234')
                alumno.set_password_recuperable('test1234')
                alumno.alumno_grupo = grupo
                alumno.save()
            alumnos_por_grupo[grado].append(alumno)

    # ══════════════════════════════════════════════════════════════
    # CARGAR CALIFICACIONES PARCIALES — Ciclo Activo (grados 1-6)
    # ══════════════════════════════════════════════════════════════
    print("\n📊 Cargando calificaciones parciales para ciclo activo...")
    boletas_creadas_activas = 0
    for grado, grupo in grupos_activos.items():
        for alumno in alumnos_por_grupo[grado]:
            for parcial in range(1, 5):  # 4 parciales
                for asig in asignaturas_por_grado[grado]:
                    # Generar nota realista (6.0 a 10.0)
                    nota = Decimal(str(round(random.uniform(6.0, 10.0), 2)))
                    
                    # Obtener docente de la asignatura
                    docente_asig = asig.docentes.first() or docente
                    
                    _, creado = BoletaParcial.objects.get_or_create(
                        alumno=alumno, grupo=grupo, asignatura=asig, parcial=parcial,
                        defaults={
                            'docente': docente_asig,
                            'nota_examen': nota,
                            'calificacion_final': nota,
                            'publicada': True,
                            'publicada_en': timezone.now(),
                        },
                    )
                    if creado:
                        boletas_creadas_activas += 1
    print(f"✅ BoletaParcial creadas (ciclo activo): {boletas_creadas_activas}")

    # ══════════════════════════════════════════════════════════════
    # 2) GRUPO DE 6° EN CICLO CERRADO — para Graduados + Historial
    # ══════════════════════════════════════════════════════════════
    print("\n📚 Configurando grupo de graduados...")
    grupo_graduado, _ = Grupo.objects.get_or_create(
        plantel=plantel, periodo=periodo_cerrado, carrera=carrera,
        grado=6, especialidad=None,
        defaults={'aula': 'Aula Graduados TEST', 'capacidad_maxima': 30},
    )
    print(f"Grupo graduado: {grupo_graduado} (id={grupo_graduado.id})")

    asignaturas_graduados = []
    for nombre_mat in ['Matemáticas VI', 'Historia de México', 'Química', 'Inglés VI']:
        asig, _ = Asignatura.objects.get_or_create(
            carrera=carrera, nombre=nombre_mat,
            defaults={'clave': nombre_mat[:6].upper(), 'creditos': 5},
        )
        grupo_graduado.asignaturas.add(asig)
        asignaturas_graduados.append(asig)
        
        # Asignar docente a la asignatura
        materia_base = nombre_mat.split()[0]
        if materia_base in docentes_por_materia:
            asig.docentes.add(docentes_por_materia[materia_base])
            # También agregar al grupo
            grupo_graduado.docentes.add(docentes_por_materia[materia_base])

    alumnos_graduados = []
    for i in range(1, 11):  # 10 egresados
        username = f'alumno.graduado.{i}'
        alumno, creado = User.objects.get_or_create(
            username=username, plantel=plantel,
            defaults={
                'rol': 'ALUMNO',
                'first_name': f'Graduado{i}',
                'last_name': 'Prueba',
                'alumno_grupo': grupo_graduado,
            },
        )
        if creado:
            alumno.set_password('test1234')
            alumno.set_password_recuperable('test1234')
            alumno.alumno_grupo = grupo_graduado
            alumno.save()
        alumnos_graduados.append(alumno)
    print(f"Alumnos graduados creados: {len(alumnos_graduados)}")

    # BoletaParcial publicadas: 4 parciales x 4 materias x 10 alumnos = 160 boletas
    print("📝 Cargando calificaciones parciales para graduados...")
    boletas_creadas_graduados = 0
    for alumno in alumnos_graduados:
        for parcial in range(1, 5):  # 4 parciales
            for asig in asignaturas_graduados:
                # Generar notas variadas (algunos con excelencia, otros regulares)
                if random.random() > 0.7:  # 30% probabilidad de nota alta
                    nota = Decimal(str(round(random.uniform(9.0, 10.0), 2)))
                else:
                    nota = Decimal(str(round(random.uniform(6.0, 8.5), 2)))
                
                docente_asig = asig.docentes.first() or docente
                
                _, creado = BoletaParcial.objects.get_or_create(
                    alumno=alumno, grupo=grupo_graduado, asignatura=asig, parcial=parcial,
                    defaults={
                        'docente': docente_asig,
                        'nota_examen': nota,
                        'calificacion_final': nota,
                        'publicada': True,
                        'publicada_en': timezone.now(),
                    },
                )
                if creado:
                    boletas_creadas_graduados += 1
    print(f"✅ BoletaParcial creadas (graduados): {boletas_creadas_graduados}")

    # ══════════════════════════════════════════════════════════════
    # 3) SESIONES DE CLASE EN VIVO — ejemplo de una clase
    # ══════════════════════════════════════════════════════════════
    print("\n🎬 Creando sesiones de clase en vivo...")
    
    # Tomar el primer grupo activo y su primer docente
    primer_grupo = grupos_activos.get(1)
    primer_docente = list(docentes_por_materia.values())[0]
    primer_asignatura = asignaturas_por_grado.get(1, [])[0] if asignaturas_por_grado.get(1) else None
    
    if primer_grupo and primer_docente and primer_asignatura:
        sesion, creada = SesionClase.objects.get_or_create(
            docente=primer_docente,
            grupo=primer_grupo,
            asignatura=primer_asignatura,
            titulo='Introducción a la Sesión de Clase',
            defaults={
                'estado': SesionClase.Estado.FINALIZADA,
                'fecha': datetime.date.today(),
            }
        )
        
        if creada:
            # Agregar bloques de contenido
            contenidos = [
                ('texto', 'Bienvenida a la clase', 'Hoy vamos a aprender sobre los conceptos fundamentales de esta materia.'),
                ('texto', 'Objetivo', 'Al final de esta clase, serás capaz de entender y aplicar los conceptos clave.'),
                ('link', 'Material de referencia', 'https://example.com/material'),
                ('actividad', 'Actividad Interactiva', 'Responde las siguientes preguntas sobre lo que hemos visto.'),
            ]
            
            for idx, (tipo, titulo, contenido) in enumerate(contenidos, 1):
                BloqueClase.objects.create(
                    sesion=sesion,
                    tipo=tipo,
                    titulo=titulo,
                    contenido=contenido,
                    orden=idx,
                )
            print(f"   ✓ Sesión '{sesion.titulo}' con {len(contenidos)} bloques")
        else:
            print(f"   ℹ Sesión ya existe")

    # ══════════════════════════════════════════════════════════════
    # RESUMEN
    # ══════════════════════════════════════════════════════════════
    total_grupos_activos = len(grupos_activos)
    total_alumnos_activos = sum(len(alumnos) for alumnos in alumnos_por_grupo.values())
    total_asignaturas_activas = sum(len(asigs) for asigs in asignaturas_por_grado.values())
    total_boletas_activas = boletas_creadas_activas
    
    total_alumnos_graduados = len(alumnos_graduados)
    total_asignaturas_graduados = len(asignaturas_graduados)
    total_boletas_graduados = boletas_creadas_graduados
    
    # Contar sesiones de clase
    total_sesiones = SesionClase.objects.filter(grupo__plantel=plantel).count()
    total_bloques = BloqueClase.objects.filter(sesion__grupo__plantel=plantel).count()
    
    print("\n" + "="*70)
    print("✅ DATOS DE PRUEBA CARGADOS EN PLANTEL 2 - EXITOSAMENTE")
    print("="*70)
    
    print(f"\n📊 CICLO ACTIVO ({periodo_activo.nombre}):")
    print(f"   • Grupos: {total_grupos_activos} (grados 1-6)")
    print(f"   • Alumnos: {total_alumnos_activos} ({3} por grado)")
    print(f"   • Asignaturas: {total_asignaturas_activas} (≈4 por grado)")
    print(f"   • Boletas Parciales: {total_boletas_activas} (4 parciales × {3} alumnos × ≈4 materias)")
    print(f"   • Docentes: {len(docentes_por_materia)}")
    
    print(f"\n📚 CICLO CERRADO ({periodo_cerrado.nombre}):")
    print(f"   • Grupos de Graduados: 1 (6° grado)")
    print(f"   • Alumnos Graduados: {total_alumnos_graduados}")
    print(f"   • Asignaturas: {total_asignaturas_graduados}")
    print(f"   • Boletas Parciales: {total_boletas_graduados} (4 × 4 × 10)")
    
    print(f"\n🎬 SESIONES DE CLASE EN VIVO:")
    print(f"   • Sesiones: {total_sesiones}")
    print(f"   • Bloques de contenido: {total_bloques}")
    
    print(f"\n🔑 USUARIOS DE PRUEBA:")
    print(f"   Alumnos activos:   alumno.g[1-6].[1-3]")
    print(f"   Alumnos graduados: alumno.graduado.[1-10]")
    print(f"   Docentes:          docente.test, docente.[materia].[1-6]")
    print(f"   Contraseña:        test1234 (todos)")
    
    print(f"\n🧪 CASOS DE PRUEBA DISPONIBLES:")
    print(f"   ✓ Promoción Masiva (6 grupos, 18 alumnos)")
    print(f"   ✓ Historial Académico de Graduados (10 alumnos, 4 parciales cada uno)")
    print(f"   ✓ Boleta Parcial (todas las materias, todos los parciales)")
    print(f"   ✓ Reporte de Calificaciones (por grupo, por materia, por parcial)")
    print(f"   ✓ Acceso por Rol (docente → su grupo, alumno → su boleta)")
    print(f"   ✓ Sesiones de Clase en Vivo (ver bloques de contenido)")
    
    print("\n" + "="*70)
    print(f"🏫 PLANTEL: {plantel.nombre} (ID={plantel.id})")
    print("="*70)