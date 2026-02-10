def temas_plantel(request):
    if request.user.is_authenticated and request.user.plantel:
        es_uni = request.user.plantel.id == 2
        return {
            'color': 'purple' if es_uni else 'blue',
            'labels': {
                'docentes': 'Catedráticos' if es_uni else 'Docentes',
                'grupos': 'Facultades' if es_uni else 'Grupos',
                'alumnos': 'Universitarios' if es_uni else 'Alumnos',
                'nivel': 'Nivel Superior' if es_uni else 'Nivel Básico',
            }
        }
    return {'color': 'blue', 'labels': {}} 