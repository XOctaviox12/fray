"""
Seed de prueba LIMPIO para Plantel 2, con PROGRESIÓN ACADÉMICA REAL (v3):

  - Borra por completo los datos de prueba anteriores antes de generar.
  - Genera 12 Periodos secuenciales alternando NON y PAR, donde solo UNO está activo.
    Ej: 2024 NON, 2024 PAR, 2025 NON (ACTIVO si aplica), ...
  - Distribuye los 6 grados correctamente por paridad:
    * Grados impares (1°, 3°, 5°): en periodos NON
    * Grados pares (2°, 4°, 6°): en periodos PAR
  - Crea grupos de CADA grado en TODOS los periodos de su paridad (grid completo),
    para poder reconstruir la progresión real de cualquier cohorte.

  PROGRESIÓN REAL (lo nuevo en v3):
    - Cada alumno actual, según su grado, tiene una "ruta" hacia atrás en el
      tiempo: grado_final en idx_actual, grado_final-1 en idx_actual-1,
      grado_final-2 en idx_actual-2, etc. — es decir, SÍ pasó por los grados
      anteriores en periodos anteriores reales (no repite el mismo grado).
    - Grado 1°: sin historial (ruta de un solo elemento, el periodo actual).
    - Grado 2°: 1 semestre histórico (su propio 1°).
    - Grado 3°: 2 semestres históricos (su propio 1° y 2°).
    - ... y así sucesivamente. El grado 6° actual llega con 5 semestres
      históricos completos.
    - El periodo del grado_final ("grado actual") queda EN CURSO: solo
      asistencia parcial, sin boletas (aún no termina el semestre).
    - Los EGRESADOS son alumnos que YA completaron su 6° grado en un periodo
      PAR histórico: su ruta completa (incluyendo el propio 6°) lleva
      boletas + asistencia completas, porque ya se graduaron. Si la cohorte
      es de las primeras (no hay suficientes periodos anteriores dentro de
      la ventana de 12), su ruta se recorta automáticamente y no incluye
      los grados más bajos (mismo criterio: sin datos inventados).

Nota técnica:
  - Asistencia.save() bloquea si periodo.activo=False.
  - Para asistencia histórica usamos bulk_create() (sin validación).

Uso:
    python manage.py shell < seed_test_data_historial_v3.py

Re-ejecutable: el bloque de limpieza borra todo anterior antes de reconstruir.
"""

import datetime
import random
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from campuses.models import Plantel
from academic.models import (
    Periodo, Carrera, Grupo, Asignatura, BoletaParcial, Asistencia,
    SesionClase, BloqueClase,
)
from users.models import User, DocenteGrupo

# ══════════════════════════════════════════════════════════════════
# 0) PLANTEL
# ══════════════════════════════════════════════════════════════════
plantel = Plantel.objects.filter(id=2).first()
if not plantel:
    print("\n❌ ERROR: No existe Plantel con id=2")
    exit(1)
print(f"\n✓ Usando plantel: {plantel} (ID={plantel.id})")


def ciclo_str(periodo):
    """String corto para DocenteGrupo.ciclo."""
    return f"{periodo.fecha_inicio.year}-{periodo.tipo}"[:20]


def crear_periodos_alternados(anio_inicio, cantidad=12, sufijo=" TEST"):
    """
    Crea 'cantidad' periodos alternados (NON, PAR, NON, PAR...) comenzando
    desde 'anio_inicio' (tipo NON). Solo el último está activo.
    Devuelve lista de Periodo en orden cronológico (más antiguo primero).
    """
    periodos = []
    ano = anio_inicio
    tipo_actual = "NON"

    for i in range(cantidad):
        if tipo_actual == "NON":
            fecha_inicio = datetime.date(ano, 8, 1)
            fecha_fin = datetime.date(ano + 1, 1, 31)
            mes_inicio, mes_fin = "Agosto", "Enero"
            anios_str = f"{ano}–{ano+1}"
        else:  # PAR
            fecha_inicio = datetime.date(ano + 1, 2, 1)
            fecha_fin = datetime.date(ano + 1, 6, 30)
            mes_inicio, mes_fin = "Febrero", "Junio"
            anios_str = f"{ano+1}"

        nombre = f"{anios_str} {mes_inicio}–{mes_fin}{sufijo}"
        activo = (i == cantidad - 1)  # Solo el último período es activo

        periodo, _ = Periodo.objects.get_or_create(
            plantel=plantel,
            nombre=nombre,
            defaults={
                "tipo": tipo_actual,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "activo": activo,
            },
        )
        periodos.append(periodo)

        # Cambiar tipo y/o año para el siguiente período
        if tipo_actual == "NON":
            tipo_actual = "PAR"
        else:  # PAR
            tipo_actual = "NON"
            ano += 1

    return periodos


def fechas_muestra(periodo, n=6):
    """n fechas repartidas dentro del rango del periodo."""
    total_dias = (periodo.fecha_fin - periodo.fecha_inicio).days
    paso = max(total_dias // (n + 1), 1)
    return [
        periodo.fecha_inicio + datetime.timedelta(days=paso * (i + 1))
        for i in range(n)
    ]


def ruta_progresion(grado_final, idx_final):
    """
    Devuelve la ruta cronológica real de un alumno que hoy está en
    'grado_final' dentro del periodo de índice 'idx_final'.

    Ej: grado_final=4, idx_final=11 -> [(1,8), (2,9), (3,10), (4,11)]

    Si no hay suficientes periodos anteriores dentro de la ventana
    (idx < 0), esos grados más bajos simplemente no se incluyen —
    no se inventan datos.
    """
    ruta = []
    for g in range(1, grado_final + 1):
        idx = idx_final - (grado_final - g)
        if idx >= 0:
            ruta.append((g, idx))
    return ruta


with transaction.atomic():

    # ══════════════════════════════════════════════════════════════
    # 1) LIMPIEZA — en orden, respetando FKs
    # ══════════════════════════════════════════════════════════════
    print("\n🧹 Limpiando datos de prueba anteriores...")

    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM academic_comentarioactividad;")
        print("   Tabla academic_comentarioactividad limpiada (vía SQL directo)")

    from academic.models import ComentarioMaterial, ComentarioTarea

    n_comentarios_material = ComentarioMaterial.objects.filter(
        material__grupo__plantel=plantel
    ).count()
    ComentarioMaterial.objects.filter(material__grupo__plantel=plantel).delete()

    n_comentarios_tarea = ComentarioTarea.objects.filter(
        tarea__grupo__plantel=plantel
    ).count()
    ComentarioTarea.objects.filter(tarea__grupo__plantel=plantel).delete()

    n_carreras = Carrera.objects.filter(plantel=plantel).count()
    Carrera.objects.filter(plantel=plantel).delete()

    n_periodos = Periodo.objects.filter(plantel=plantel).count()
    Periodo.objects.filter(plantel=plantel).delete()

    n_usuarios = User.objects.filter(
        plantel=plantel, rol__in=["ALUMNO", "DOCENTE"]
    ).filter(
        Q(username__startswith="alumno.")
        | Q(username__startswith="docente.")
        | Q(username__startswith="egresado.")
    ).count()
    User.objects.filter(
        plantel=plantel, rol__in=["ALUMNO", "DOCENTE"]
    ).filter(
        Q(username__startswith="alumno.")
        | Q(username__startswith="docente.")
        | Q(username__startswith="egresado.")
    ).delete()

    print(f"   Comentarios Material eliminados: {n_comentarios_material}")
    print(f"   Comentarios Tarea eliminados: {n_comentarios_tarea}")
    print(f"   Carreras eliminadas: {n_carreras}")
    print(f"   Periodos eliminados: {n_periodos}")
    print(f"   Usuarios de prueba eliminados: {n_usuarios}")

    # ══════════════════════════════════════════════════════════════
    # 2) CARRERA
    # ══════════════════════════════════════════════════════════════
    nivel_carrera = (
        "PREPARATORIA" if plantel.nivel_educativo == "BASICA" else "UNIVERSIDAD"
    )
    nombre_carrera = (
        "Bachillerato General"
        if nivel_carrera == "PREPARATORIA"
        else "Licenciatura en Sistemas"
    )

    carrera = Carrera.objects.create(
        plantel=plantel,
        nombre=nombre_carrera,
        nivel=nivel_carrera,
        clave_rvoe=f"TEST-{plantel.id:03d}",
    )
    print(f"\nCarrera: {carrera.nombre} ({carrera.get_nivel_display()})")

    docente, _ = User.objects.get_or_create(
        username="docente.test",
        plantel=plantel,
        defaults={"rol": "DOCENTE", "first_name": "Docente", "last_name": "Prueba"},
    )
    if not docente.has_usable_password():
        docente.set_password("test1234")
        docente.set_password_recuperable("test1234")
        docente.save()

    # ══════════════════════════════════════════════════════════════
    # 3) DOCENTES POR MATERIA
    # ══════════════════════════════════════════════════════════════
    docentes_por_materia = {}
    for i, nombre_mat in enumerate(
        ["Matemáticas", "Historia", "Química", "Inglés", "Español", "Física"], 1
    ):
        docente_mat, _ = User.objects.get_or_create(
            username=f"docente.{nombre_mat.lower()}.{i}",
            plantel=plantel,
            defaults={
                "rol": "DOCENTE",
                "first_name": f"Prof. {nombre_mat}",
                "last_name": "Prueba",
            },
        )
        if not docente_mat.has_usable_password():
            docente_mat.set_password("test1234")
            docente_mat.set_password_recuperable("test1234")
            docente_mat.save()
        docentes_por_materia[nombre_mat] = docente_mat
        print(f"Docente: {docente_mat.username}")

    # ══════════════════════════════════════════════════════════════
    # 4) ASIGNATURAS POR GRADO/SEMESTRE (1 a 6)
    # ══════════════════════════════════════════════════════════════
    materias_por_grado = {
        1: ["Matemáticas I", "Historia de México", "Química", "Inglés I"],
        2: ["Matemáticas II", "Historia Universal", "Química II", "Inglés II"],
        3: ["Matemáticas III", "Historia Moderna", "Física", "Inglés III"],
        4: ["Matemáticas IV", "Historia Contemporánea", "Física II", "Inglés IV"],
        5: ["Matemáticas V", "Historia de América", "Química III", "Inglés V"],
        6: ["Matemáticas VI", "Historia de México", "Química", "Inglés VI"],
    }
    asignaturas_por_grado = {}
    for grado, materias in materias_por_grado.items():
        asignaturas_por_grado[grado] = []
        for nombre_mat in materias:
            asig, _ = Asignatura.objects.get_or_create(
                carrera=carrera,
                nombre=nombre_mat,
                defaults={"clave": nombre_mat[:6].upper(), "creditos": 5},
            )
            asignaturas_por_grado[grado].append(asig)
        print(f"Asignaturas semestre {grado}: {len(asignaturas_por_grado[grado])}")

    # ══════════════════════════════════════════════════════════════
    # 5) PERIODOS: 12 alternados (NON, PAR, NON...) desde 2024
    # ══════════════════════════════════════════════════════════════
    periodos = crear_periodos_alternados(anio_inicio=2024, cantidad=12)
    periodo_activo = periodos[-1]

    print("\n📅 Periodos generados (12 periodos alternados NON/PAR):")
    for i, p in enumerate(periodos, 1):
        estado = "ACTIVO" if p.activo else "cerrado"
        print(f"   {i:2}. {p.nombre}  [{estado}]")

    print(f"\n✓ Periodo activo: {periodo_activo.nombre} (tipo={periodo_activo.tipo})")

    periodos_non = [i for i, p in enumerate(periodos) if p.tipo == "NON"]
    periodos_par = [i for i, p in enumerate(periodos) if p.tipo == "PAR"]

    print(f"\nPeriodos NON (impares: 1°, 3°, 5°): índices {periodos_non}")
    print(f"Periodos PAR (pares: 2°, 4°, 6°): índices {periodos_par}")

    # ══════════════════════════════════════════════════════════════
    # 6) ALUMNOS ACTUALES — 3 por grado
    # ══════════════════════════════════════════════════════════════
    alumnos_por_grado = {}
    for grado in range(1, 7):
        alumnos_por_grado[grado] = []
        for i in range(1, 4):
            username = f"alumno.g{grado}.{i}"
            alumno, creado = User.objects.get_or_create(
                username=username,
                plantel=plantel,
                defaults={
                    "rol": "ALUMNO",
                    "first_name": f"Alumno{grado}{i}",
                    "last_name": "Prueba",
                },
            )
            if creado:
                alumno.set_password("test1234")
                alumno.set_password_recuperable("test1234")
                alumno.save()
            alumnos_por_grado[grado].append(alumno)
        print(f"Alumnos semestre {grado}: {len(alumnos_por_grado[grado])}")

    # ══════════════════════════════════════════════════════════════
    # 6b) ALUMNOS EGRESADOS — uno por cada generación PAR histórica
    # ══════════════════════════════════════════════════════════════
    print("\n👨‍🎓 Creando alumnos egresados (generaciones graduadas)...")
    alumnos_egresados = {}  # {idx_periodo_graduacion: [alumnos]}

    for idx_periodo in periodos_par[:-1]:  # todos los PAR excepto el actual
        alumnos_egresados[idx_periodo] = []
        periodo = periodos[idx_periodo]
        for i in range(1, 4):
            username = f"egresado.{periodo.tipo}.{periodo.fecha_inicio.year}.{i}"
            alumno, creado = User.objects.get_or_create(
                username=username,
                plantel=plantel,
                defaults={
                    "rol": "ALUMNO",
                    "first_name": f"Egresado{i}",
                    "last_name": f"{periodo.fecha_inicio.year}",
                },
            )
            if creado:
                alumno.set_password("test1234")
                alumno.set_password_recuperable("test1234")
                alumno.save()
            alumnos_egresados[idx_periodo].append(alumno)
        print(f"   {len(alumnos_egresados[idx_periodo])} egresados → {periodo.nombre}")

    # ══════════════════════════════════════════════════════════════
    # 7) GRID COMPLETO DE GRUPOS (todos los grados x todos los periodos
    #    de su paridad) — necesario para poder reconstruir cualquier ruta
    # ══════════════════════════════════════════════════════════════
    print("\n📚 Creando grupos (grid completo) por grado y período de su paridad...")

    grupos_por_grado = {}  # {grado: {periodo_idx: grupo}}
    docentegrupo_totales = 0

    for grado in range(1, 7):
        grupos_por_grado[grado] = {}
        indices_periodos = periodos_non if grado % 2 == 1 else periodos_par

        for idx_periodo in indices_periodos:
            periodo = periodos[idx_periodo]

            grupo, _ = Grupo.objects.get_or_create(
                plantel=plantel,
                periodo=periodo,
                carrera=carrera,
                grado=grado,
                especialidad=None,
                defaults={
                    "aula": f"Aula {grado} ({periodo.get_display_name(corto=True)})",
                    "capacidad_maxima": 30,
                },
            )
            grupos_por_grado[grado][idx_periodo] = grupo

            for asig in asignaturas_por_grado[grado]:
                grupo.asignaturas.add(asig)
                materia_base = asig.nombre.split()[0]
                docente_mat = docentes_por_materia.get(materia_base)
                if docente_mat:
                    asig.docentes.add(docente_mat)
                    grupo.docentes.add(docente_mat)
                    _, dg_creado = DocenteGrupo.objects.get_or_create(
                        docente=docente_mat,
                        grupo=grupo,
                        asignatura=asig,
                        ciclo=ciclo_str(periodo),
                        defaults={"activo": periodo.activo},
                    )
                    if dg_creado:
                        docentegrupo_totales += 1

            print(f"   Grado {grado}° en {periodo.nombre}: grupo id={grupo.id}")

    print(f"\n✅ DocenteGrupo creadas: {docentegrupo_totales}")

    # ══════════════════════════════════════════════════════════════
    # 8) idx_actual por grado (dónde está HOY cada cohorte actual)
    # ══════════════════════════════════════════════════════════════
    idx_actual_por_grado = {}
    for grado in range(1, 7):
        if grado % 2 == 1:  # NON impares: penúltimo NON (aún no marcado activo)
            idx_actual_por_grado[grado] = periodos_non[-2]
        else:  # PAR pares: el activo
            idx_actual_por_grado[grado] = periodos_par[-1]

    print("\n🎓 Asignando alumnos actuales a su grupo del periodo en curso...")
    for grado in range(1, 7):
        idx_actual = idx_actual_por_grado[grado]
        grupo_actual = grupos_por_grado[grado][idx_actual]
        for alumno in alumnos_por_grado[grado]:
            alumno.alumno_grupo = grupo_actual
            alumno.save()
        print(f"   {len(alumnos_por_grado[grado])} alumnos → {grupo_actual}")

    print("\n👨‍🎓 Asignando egresados a su grupo de 6° (graduación)...")
    for idx_periodo in periodos_par[:-1]:
        grupo_6 = grupos_por_grado[6][idx_periodo]
        for alumno in alumnos_egresados[idx_periodo]:
            alumno.alumno_grupo = grupo_6
            alumno.save()
        print(f"   {len(alumnos_egresados[idx_periodo])} egresados → {grupo_6}")

    # ══════════════════════════════════════════════════════════════
    # 9) CONSTRUCCIÓN DE HISTORIAL — progresión real por ruta
    # ══════════════════════════════════════════════════════════════
    boletas_totales = 0
    asistencias_totales = 0

    def crear_boletas_y_asistencia_completas(alumno, grado, idx_periodo):
        global boletas_totales, asistencias_totales
        periodo = periodos[idx_periodo]
        grupo = grupos_por_grado[grado][idx_periodo]

        for parcial in range(1, 5):
            for asig in asignaturas_por_grado[grado]:
                nota = Decimal(str(round(random.uniform(6.0, 10.0), 2)))
                docente_asig = asig.docentes.first() or docente
                _, creado = BoletaParcial.objects.get_or_create(
                    alumno=alumno,
                    grupo=grupo,
                    asignatura=asig,
                    parcial=parcial,
                    defaults={
                        "docente": docente_asig,
                        "nota_examen": nota,
                        "calificacion_final": nota,
                        "publicada": True,
                        "publicada_en": timezone.now(),
                    },
                )
                if creado:
                    boletas_totales += 1

        fechas = fechas_muestra(periodo, n=6)
        nuevas = []
        for asig in asignaturas_por_grado[grado]:
            for fecha in fechas:
                estado = "P" if random.random() < 0.85 else random.choice(["A", "R"])
                nuevas.append(
                    Asistencia(
                        alumno=alumno,
                        grupo=grupo,
                        asignatura=asig,
                        periodo=periodo,
                        fecha=fecha,
                        estado=estado,
                        parcial=1,
                    )
                )
        if nuevas:
            Asistencia.objects.bulk_create(nuevas, ignore_conflicts=True)
            asistencias_totales += len(nuevas)

    def crear_asistencia_parcial_en_curso(alumno, grado, idx_periodo, n=4):
        global asistencias_totales
        periodo = periodos[idx_periodo]
        grupo = grupos_por_grado[grado][idx_periodo]
        fechas = fechas_muestra(periodo, n=n)
        nuevas = []
        for asig in asignaturas_por_grado[grado]:
            for fecha in fechas:
                estado = "P" if random.random() < 0.85 else random.choice(["A", "R"])
                nuevas.append(
                    Asistencia(
                        alumno=alumno,
                        grupo=grupo,
                        asignatura=asig,
                        periodo=periodo,
                        fecha=fecha,
                        estado=estado,
                        parcial=1,
                    )
                )
        if nuevas:
            Asistencia.objects.bulk_create(nuevas, ignore_conflicts=True)
            asistencias_totales += len(nuevas)

    # ── Alumnos actuales: ruta completa, el último tramo (grado actual)
    #    queda EN CURSO (solo asistencia parcial, sin boletas) ──
    print("\n📊 Generando historial (progresión real) para alumnos actuales...")
    for grado in range(1, 7):
        idx_actual = idx_actual_por_grado[grado]
        ruta = ruta_progresion(grado, idx_actual)
        for alumno in alumnos_por_grado[grado]:
            for g, idx in ruta:
                if g == grado and idx == idx_actual:
                    # tramo en curso: sin boletas, asistencia parcial
                    crear_asistencia_parcial_en_curso(alumno, g, idx, n=4)
                else:
                    crear_boletas_y_asistencia_completas(alumno, g, idx)
        n_hist = len(ruta) - 1
        print(f"   Grado {grado}°: {n_hist} semestre(s) histórico(s) + 1 en curso")

    # ── Egresados: ruta completa incluyendo el propio 6° (ya graduados,
    #    todo el tramo lleva boletas + asistencia completas) ──
    print("\n📜 Generando historial completo para egresados (incluye su 6°)...")
    for idx_periodo in periodos_par[:-1]:
        ruta = ruta_progresion(6, idx_periodo)
        for alumno in alumnos_egresados[idx_periodo]:
            for g, idx in ruta:
                crear_boletas_y_asistencia_completas(alumno, g, idx)
        print(
            f"   Generación {periodos[idx_periodo].nombre}: "
            f"{len(ruta)} semestre(s) en el historial"
        )

    print(f"\n   ✅ BoletaParcial creadas: {boletas_totales}")
    print(f"   ✅ Asistencias creadas: {asistencias_totales}")

    # ══════════════════════════════════════════════════════════════
    # 10) SESIÓN DE CLASE EN VIVO — ejemplo
    # ══════════════════════════════════════════════════════════════
    print("\n🎬 Creando sesión de clase en vivo de ejemplo...")

    idx_ejemplo = periodos_par[-1]
    grupo_ejemplo = grupos_por_grado[2][idx_ejemplo]
    docente_ejemplo = list(docentes_por_materia.values())[0]
    asig_ejemplo = asignaturas_por_grado[2][0]

    if grupo_ejemplo and docente_ejemplo and asig_ejemplo:
        sesion, creada = SesionClase.objects.get_or_create(
            docente=docente_ejemplo,
            grupo=grupo_ejemplo,
            asignatura=asig_ejemplo,
            titulo="Introducción a la Sesión de Clase",
            defaults={
                "estado": SesionClase.Estado.FINALIZADA,
                "fecha": datetime.date.today(),
            },
        )
        if creada:
            contenidos = [
                ("texto", "Bienvenida", "Hoy vamos a aprender conceptos fundamentales."),
                ("texto", "Objetivo", "Serás capaz de entender y aplicar los conceptos clave."),
                ("link", "Material", "https://example.com/material"),
                ("actividad", "Actividad", "Responde sobre lo visto."),
            ]
            for idx, (tipo, titulo, contenido) in enumerate(contenidos, 1):
                BloqueClase.objects.create(
                    sesion=sesion, tipo=tipo, titulo=titulo, contenido=contenido, orden=idx
                )
            print(f"   ✓ Sesión con {len(contenidos)} bloques")
        else:
            print("   ℹ Sesión ya existe")

    # ══════════════════════════════════════════════════════════════
    # 11) RESUMEN
    # ══════════════════════════════════════════════════════════════
    total_grupos = Grupo.objects.filter(plantel=plantel).count()
    total_boletas = BoletaParcial.objects.filter(grupo__plantel=plantel).count()
    total_asistencias = Asistencia.objects.filter(grupo__plantel=plantel).count()
    total_dg = DocenteGrupo.objects.filter(grupo__plantel=plantel).count()

    print("\n" + "=" * 80)
    print("✅ DATOS DE PRUEBA CON PROGRESIÓN REAL RECONSTRUIDOS EN PLANTEL 2")
    print("=" * 80)

    print(f"\n📚 Totales en el plantel:")
    print(f"   • Períodos: {len(periodos)} (NON/PAR alternados)")
    print(f"   • Grupos (grid completo): {total_grupos}")
    print(f"   • BoletaParcial: {total_boletas}")
    print(f"   • Asistencias: {total_asistencias}")
    print(f"   • DocenteGrupo: {total_dg}")

    print(f"\n🔑 USUARIOS DE PRUEBA:")
    print(f"   Alumnos actuales: alumno.g[1-6].[1-3]  (progresión real, grado1 sin historial)")
    print(f"   Egresados:        egresado.PAR.[año].[1-3]  (historial completo hasta 6°)")
    print(f"   Docentes:         docente.test, docente.[materia].[1-6]")
    print(f"   Contraseña:       test1234 (todos)")

    print(f"\n⏱️  PERÍODO ACTIVO: {periodo_activo.nombre} ({periodo_activo.tipo})")

    print("\n" + "=" * 80)
    print(f"🏫 PLANTEL: {plantel.nombre} (ID={plantel.id})")
    print("=" * 80)