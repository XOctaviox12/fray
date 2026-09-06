(function($) {
    $(document).ready(function() {
        // Cuando cambie el campo de rol, recargamos la página para actualizar la preview
        $('#id_rol').change(function() {
            var rol = $(this).val();
            var plantel = $('#id_plantel').val() || '';
            // Recargar la misma página con los parámetros
            var url = window.location.pathname + '?rol=' + encodeURIComponent(rol) + '&plantel=' + encodeURIComponent(plantel);
            window.location.href = url;
        });

        // Cuando cambie el plantel, también recargamos (si el rol es DOCENTE)
        $('#id_plantel').change(function() {
            var rol = $('#id_rol').val();
            if (rol === 'DOCENTE') {
                var plantel = $(this).val() || '';
                var url = window.location.pathname + '?rol=' + encodeURIComponent(rol) + '&plantel=' + encodeURIComponent(plantel);
                window.location.href = url;
            }
        });
    });
})(django.jQuery);