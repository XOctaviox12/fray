document.addEventListener('DOMContentLoaded', function () {

    console.log(
        '✅ credenciales_preview.js cargado y ejecutándose.'
    );

    const rolField =
        document.querySelector('[name="rol"]') ||
        document.getElementById('id_rol');

    const plantelField =
        document.querySelector('[name="plantel"]') ||
        document.getElementById('id_plantel');

    const usernamePreview =
        document.querySelector('[name="username_preview"]') ||
        document.getElementById('id_username_preview');

    const passwordPreview =
        document.querySelector('[name="password_preview"]') ||
        document.getElementById('id_password_preview');


    console.log('Rol:', rolField);
    console.log('Plantel:', plantelField);
    console.log(
        'Username preview:',
        usernamePreview
    );
    console.log(
        'Password preview:',
        passwordPreview
    );


    if (
        !rolField ||
        !plantelField ||
        !usernamePreview ||
        !passwordPreview
    ) {

        console.error(
            '❌ No se encontraron todos los campos necesarios.'
        );

        return;
    }


    // ========================================================
    // DETECTAR SI ES CREACIÓN O EDICIÓN
    // ========================================================

    const isAdd =
        window.location.pathname.endsWith('/add/');


    // ========================================================
    // DATOS ORIGINALES
    // ========================================================

    const originalRole =
        rolField.dataset.originalRole || '';

    const originalPlantel =
        plantelField.dataset.originalPlantel || '';


    const originalUsername =
        usernamePreview.value || '';


    const originalPassword =
        passwordPreview.value || '';


    let loading = false;


    // ========================================================
    // LIMPIAR
    // ========================================================

    function limpiarPreview() {

        usernamePreview.value = '';

        passwordPreview.value = '';
    }


    // ========================================================
    // RESTAURAR CREDENCIALES ORIGINALES
    // ========================================================

    function restaurarOriginal() {

        usernamePreview.value =
            originalUsername;

        passwordPreview.value =
            originalPassword;
    }


    // ========================================================
    // DETERMINAR SI NECESITA NUEVAS CREDENCIALES
    // ========================================================

    function necesitaCredencialesGeneradas() {

        // -----------------------------------------------
        // CREACIÓN
        // -----------------------------------------------

        if (isAdd) {

            return (
                rolField.value === 'ALUMNO' ||
                rolField.value === 'DOCENTE'
            );
        }


        // -----------------------------------------------
        // EDICIÓN
        // -----------------------------------------------

        const cambioRol =
            rolField.value !== originalRole;


        const cambioPlantel =
            plantelField.value !== originalPlantel;


        return (

            (
                cambioRol &&
                (
                    rolField.value === 'ALUMNO' ||
                    rolField.value === 'DOCENTE'
                )
            )

            ||

            (
                rolField.value === 'DOCENTE' &&
                cambioPlantel
            )

        );
    }


    // ========================================================
    // ACTUALIZAR PREVIEW
    // ========================================================

    async function actualizarPreview() {

        const rol =
            rolField.value;


        const plantel =
            plantelField.value;


        console.log(
            '🔄 Actualizando credenciales:',
            {
                rol: rol,
                plantel: plantel,
                isAdd: isAdd,
                originalRole: originalRole,
                originalPlantel: originalPlantel
            }
        );


        if (loading) {

            return;
        }


        // ====================================================
        // SI ES EDICIÓN Y NO CAMBIÓ NADA
        // ====================================================

        if (
            !isAdd &&
            rol === originalRole &&
            plantel === originalPlantel
        ) {

            restaurarOriginal();

            return;
        }


        // ====================================================
        // SI NO NECESITA CREDENCIALES
        // ====================================================

        if (
            !necesitaCredencialesGeneradas()
        ) {

            limpiarPreview();

            return;
        }


        // ====================================================
        // DOCENTE SIN PLANTEL
        // ====================================================

        if (
            rol === 'DOCENTE' &&
            !plantel
        ) {

            usernamePreview.value =
                '⚠️ Selecciona un plantel';

            passwordPreview.value = '';

            return;
        }


        loading = true;


        // ====================================================
        // URL
        // ====================================================

        const url =
            '/admin/users/user/preview-credenciales/' +
            '?rol=' +
            encodeURIComponent(rol) +
            '&plantel=' +
            encodeURIComponent(
                plantel || ''
            );


        console.log(
            '🌐 Consultando:',
            url
        );


        try {

            const response =
                await fetch(
                    url,
                    {
                        method: 'GET',

                        headers: {
                            'X-Requested-With':
                                'XMLHttpRequest',

                            'Accept':
                                'application/json'
                        },

                        credentials:
                            'same-origin'
                    }
                );


            const contentType =
                response.headers.get(
                    'content-type'
                ) || '';


            const text =
                await response.text();


            // =================================================
            // ERROR HTTP
            // =================================================

            if (!response.ok) {

                console.error(
                    '❌ Error HTTP:',
                    response.status,
                    text.substring(0, 300)
                );

                throw new Error(
                    'HTTP ' +
                    response.status
                );
            }


            // =================================================
            // VALIDAR JSON
            // =================================================

            if (
                !contentType.includes(
                    'application/json'
                )
            ) {

                console.error(
                    '❌ El servidor no devolvió JSON.',
                    text.substring(0, 500)
                );

                throw new Error(
                    'La respuesta no es JSON. '
                    +
                    'Revisa la URL del endpoint.'
                );
            }


            // =================================================
            // PARSEAR JSON
            // =================================================

            const data =
                JSON.parse(text);


            console.log(
                '✅ Credenciales recibidas:',
                data
            );


            // =================================================
            // MOSTRAR PREVIEW
            // =================================================

            usernamePreview.value =
                data.username || '';


            passwordPreview.value =
                data.password || '';


        } catch (error) {

            console.error(
                '❌ Error obteniendo credenciales:',
                error
            );

        } finally {

            loading = false;
        }
    }


    // ========================================================
    // CAMBIO DE ROL
    // ========================================================

    rolField.addEventListener(
        'change',
        function () {

            console.log(
                '👤 Cambio de rol:',
                rolField.value
            );

            actualizarPreview();
        }
    );


    // ========================================================
    // CAMBIO DE PLANTEL
    // ========================================================

    plantelField.addEventListener(
        'change',
        function () {

            console.log(
                '🏫 Cambio de plantel:',
                plantelField.value
            );

            actualizarPreview();
        }
    );


    // ========================================================
    // INICIALIZAR
    // ========================================================

    actualizarPreview();

});