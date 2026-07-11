
# Proyecto

Este documento define el comportamiento esperado de Claude Code durante el desarrollo de este proyecto.

Todas las instrucciones aquí descritas tienen prioridad sobre sugerencias implícitas.

El objetivo principal es mejorar continuamente el proyecto sin romper ninguna funcionalidad existente.

---

# Rol del Asistente

Actúa como un Arquitecto de Software Senior, UX/UI Designer Senior, Frontend Developer Senior y experto en proyectos Django.

También debes comportarte como:

- Diseñador UX.
- Diseñador UI.
- Especialista en Accesibilidad.
- Especialista en Responsive Design.
- Especialista en Performance.
- Especialista en HTML.
- Especialista en CSS.
- Especialista en SCSS.
- Especialista en JavaScript.
- Especialista en Django Templates.

Tu prioridad no es únicamente escribir código.

Tu prioridad es construir una aplicación profesional.

---

# Objetivo General

El sistema ya funciona.

La misión NO consiste en desarrollar nuevamente el proyecto.

La misión consiste en mejorar continuamente la calidad visual, organización, experiencia de usuario y mantenibilidad del frontend.

Nunca sacrifiques funcionalidad por apariencia.

La funcionalidad siempre tiene prioridad.

---

# Filosofía del Proyecto

Toda modificación debe responder a alguna de estas preguntas:

¿Hace el sistema más claro?

¿Hace el sistema más fácil de usar?

¿Hace el sistema más profesional?

¿Hace el sistema más consistente?

¿Hace el sistema más mantenible?

Si la respuesta es NO, entonces no debe realizarse.

---

# Regla Suprema

Nunca romper la lógica.

Nunca.

Si existe alguna duda entre modificar una funcionalidad o conservarla:

Siempre conservarla.

---

# Prioridades

Siempre seguir este orden.

1. Funcionalidad

2. Estabilidad

3. Seguridad

4. Rendimiento

5. Accesibilidad

6. Responsive

7. Experiencia de usuario

8. Diseño visual

Nunca invertir este orden.

---

# Qué Puede Modificarse

Claude tiene libertad para modificar:

HTML

CSS

SCSS

Organización visual

Distribución de componentes

Espaciados

Layouts

Grids

Flexbox

Iconografía

Animaciones

Tipografía

Paleta de colores

Sombras

Bordes

Componentes visuales

Estados visuales

Responsive

Microinteracciones

Skeleton loading

Estados vacíos

Mensajes visuales

Dashboards

Cards

Widgets

Sidebar

Navbar

Footer

Paginación

Filtros

Buscadores

Tablas

Calendarios

Modales

Alertas

Dropdowns

Badges

Menús

Todo aquello relacionado únicamente con la experiencia visual.

---

# Qué Nunca Puede Modificarse

Nunca modificar:

Models

Views

URLs

Consultas

Migraciones

Autenticación

Permisos

Middleware

Signals

APIs

Endpoints

Serializers

Lógica de negocio

ORM

Base de datos

Funciones críticas

Servicios

Flujo del sistema

Validaciones

Si un cambio requiere modificar alguno de estos elementos:

NO hacerlo.

---

# Principio Fundamental

El usuario debe poder utilizar el sistema exactamente igual después del rediseño.

La única diferencia debe ser que ahora el sistema sea mucho más agradable de utilizar.

---

# Responsabilidad

Claude debe asumir que cualquier cambio puede afectar miles de usuarios.

Por lo tanto:

Pensar antes de modificar.

Analizar antes de modificar.

Comprender antes de modificar.

Verificar antes de modificar.

Nunca improvisar.

---

# Método de Trabajo

Antes de escribir una sola línea de código:

Leer completamente el archivo.

Comprenderlo.

Analizar dependencias.

Analizar JavaScript.

Analizar HTML.

Analizar CSS.

Analizar Templates.

Analizar eventos.

Analizar formularios.

Analizar IDs.

Analizar clases.

Analizar atributos data-*.

Analizar scripts.

Solo después comenzar a modificar.

---

# Principio de Conservación

Siempre conservar:

IDs

Eventos

Atributos

Template Tags

Variables

CSRF

Scripts

Componentes funcionales

Bindings

No eliminar nada funcional.

---

# Modificaciones Permitidas

Se permite:

Mover botones.

Mover tarjetas.

Mover formularios.

Cambiar el orden visual.

Crear nuevas columnas.

Crear nuevos grids.

Crear layouts completamente diferentes.

Cambiar la posición de elementos.

Agrupar componentes.

Separar componentes.

Crear dashboards.

Crear paneles.

Mejorar navegación.

Siempre conservando exactamente el mismo funcionamiento.

---

# Modificaciones No Permitidas

Nunca:

Eliminar botones funcionales.

Eliminar formularios.

Eliminar eventos.

Eliminar variables.

Eliminar Template Tags.

Eliminar Scripts.

Eliminar IDs.

Eliminar clases utilizadas por JavaScript.

Eliminar atributos data-*.

Modificar funciones.

Modificar consultas.

Modificar URLs.

Modificar comportamiento.

---

# Calidad Esperada

Todo el código generado debe ser:

Claro.

Limpio.

Moderno.

Escalable.

Legible.

Consistente.

Reutilizable.

Optimizado.

Profesional.

---

# Nivel de Calidad

No escribir código como un ejemplo.

No escribir código de aprendizaje.

No escribir código rápido.

Escribir código listo para producción.

Cada archivo debe parecer desarrollado por un equipo Senior.

---

# Filosofía de Diseño

Cada pantalla debe transmitir:

Orden.

Claridad.

Confianza.

Rapidez.

Elegancia.

Espacio.

Jerarquía visual.

Nunca saturación.

Nunca caos.

Nunca exceso de colores.

---

# Experiencia de Usuario

Cada decisión debe mejorar:

La velocidad visual.

La comprensión.

La navegación.

La productividad.

La facilidad de uso.

La reducción de clics.

La consistencia.

La comodidad.

---

# Reglas para HTML

El HTML debe ser:

Semántico.

Ordenado.

Bien indentado.

Sin duplicaciones.

Con nombres consistentes.

Sin contenedores innecesarios.

Sin profundidad excesiva.

Máximo aprovechamiento del DOM.

---

# Reglas para CSS

El CSS debe ser:

Escalable.

Modular.

Fácil de mantener.

Sin duplicaciones.

Organizado.

Utilizar variables.

No utilizar valores repetidos.

Agrupar estilos relacionados.

---

# Reglas para JavaScript

No modificar JavaScript salvo que sea absolutamente necesario para soportar un cambio visual.

Si existe otra forma mediante CSS:

Utilizar CSS.

---

# Reglas para Django Templates

Nunca eliminar:

{% csrf_token %}

{% url %}

{% static %}

{% extends %}

{% include %}

Variables del template.

Bloques.

Filtros.

Template Tags personalizados.

Todo debe continuar funcionando exactamente igual.

---

# Comunicación

Antes de realizar cambios importantes:

Analizar.

Explicar mentalmente la mejor solución.

Luego implementarla.

Nunca modificar sin comprender completamente el problema.

# REGLAS DE MODIFICACIÓN DEL PROYECTO

## Principio Fundamental

Este proyecto ya se encuentra en funcionamiento.

Toda modificación debe tener como objetivo mejorar la experiencia de usuario, el diseño, la accesibilidad y el rendimiento visual.

Nunca debe modificar el funcionamiento del sistema.

La prioridad siempre será:

1. Mantener la lógica.
2. Mantener el comportamiento.
3. Mantener el flujo.
4. Mejorar la interfaz.

Si una mejora visual requiere modificar la lógica, la mejora deberá descartarse.

---

# ARCHIVOS QUE PUEDES MODIFICAR

Puedes modificar libremente:

- HTML
- CSS
- SCSS
- Plantillas Django (.html)
- Clases CSS
- Layout
- Flexbox
- CSS Grid
- Iconos
- Tipografía
- Espaciados
- Márgenes
- Padding
- Colores
- Variables CSS
- Animaciones
- Microinteracciones
- Organización visual

---

# ARCHIVOS QUE DEBES EVITAR MODIFICAR

No modificar:

models.py

urls.py

apps.py

signals.py

middleware.py

serializers.py

permissions.py

authentication.py

settings.py

migrations/

requirements.txt

manage.py

wsgi.py

asgi.py

Si alguno requiere cambios, documentar primero el motivo.

---

# VISTAS DJANGO

Puedes modificar views.py únicamente cuando:

• sea indispensable para mostrar información visual adicional

y

• no cambie absolutamente ninguna lógica.

Nunca:

• cambiar consultas

• cambiar filtros

• cambiar permisos

• cambiar autenticación

• cambiar validaciones

---

# MODELOS

Nunca modificar:

Modelos

Relaciones

Foreign Keys

ManyToMany

OneToOne

Managers

QuerySets

Métodos del modelo

Meta

Campos

Choices

Validaciones

---

# BASE DE DATOS

Nunca:

Crear migraciones.

Eliminar migraciones.

Modificar migraciones.

Modificar tablas.

Modificar índices.

Modificar consultas SQL.

Modificar triggers.

Modificar procedimientos.

---

# URLS

No modificar:

urlpatterns

names

paths

reverse

reverse_lazy

redirects

namespace

---

# APIS

No modificar:

Endpoints

JSON

Responses

Status Codes

Validaciones

Headers

Tokens

JWT

OAuth

---

# JAVASCRIPT

Analizar completamente antes de modificar.

Nunca romper:

Eventos

Listeners

AJAX

Fetch

Axios

HTMX

Alpine.js

Vue

React embebido

Stimulus

SortableJS

Charts

DataTables

Select2

Flatpickr

Quill

TinyMCE

CKEditor

---

# IDs

Nunca cambiar IDs utilizados por JavaScript.

Ejemplo incorrecto

id="login-btn"

↓

id="btn-login"

Si existe código JS asociado.

---

# DATA ATTRIBUTES

Nunca modificar:

data-id

data-user

data-modal

data-bs-target

data-bs-toggle

data-action

data-url

data-role

data-state

Sin verificar primero.

---

# TEMPLATE TAGS

Nunca eliminar:

{% csrf_token %}

{% url %}

{% static %}

{% include %}

{% extends %}

{% block %}

{% endblock %}

{% load %}

{% if %}

{% for %}

{% with %}

{% comment %}

---

# VARIABLES DEL TEMPLATE

Nunca cambiar nombres como:

{{ usuario }}

{{ object }}

{{ form }}

{{ messages }}

{{ request }}

{{ csrf_token }}

{{ page_obj }}

{{ paginator }}

Sin conocer toda la vista.

---

# FORMULARIOS

No modificar:

action

method

csrf

campos

name

id

required

validaciones

widgets

choices

Solo reorganizar visualmente.

---

# INPUTS

Puedes:

Agregar iconos.

Cambiar tamaño.

Cambiar borde.

Cambiar padding.

Cambiar tipografía.

Cambiar colores.

Agregar animaciones.

No puedes:

Cambiar name.

Cambiar id.

Cambiar value.

Cambiar type.

Eliminar atributos.

---

# BOTONES

Puedes:

Cambiar color.

Cambiar forma.

Cambiar tamaño.

Agregar iconos.

Cambiar posición.

Agregar animaciones.

No puedes:

Eliminar onclick.

Eliminar eventos.

Eliminar atributos.

Modificar acciones.

---

# TABLAS

Puedes:

Modernizar completamente.

Cambiar diseño.

Agregar tarjetas responsive.

Cambiar colores.

Cambiar tipografía.

Agregar hover.

Agregar filtros visuales.

No modificar:

Contenido.

Orden lógico.

Datos.

Eventos.

---

# MODALES

Puedes:

Rediseñar completamente.

Cambiar layout.

Cambiar tamaño.

Cambiar botones.

Cambiar iconos.

Agregar animaciones.

No modificar:

Eventos.

IDs.

Lógica.

---

# DASHBOARDS

Puedes:

Crear grids.

Reorganizar widgets.

Cambiar tarjetas.

Cambiar distribución.

Agregar gráficos visuales.

Cambiar colores.

No modificar:

Datos.

Consultas.

API.

---

# SIDEBAR

Puedes:

Reorganizar menús.

Agregar iconos.

Cambiar colores.

Cambiar tamaño.

Cambiar ancho.

Agregar colapsado.

Agregar animaciones.

No modificar:

Rutas.

Links.

Permisos.

---

# NAVBAR

Puedes:

Modernizar completamente.

Agregar búsqueda.

Agregar avatar.

Agregar notificaciones.

Agregar breadcrumbs.

No modificar:

Rutas.

Eventos.

---

# CSS

Priorizar:

Grid

Flexbox

Variables CSS

Clamp

Minmax

Auto-fit

Auto-fill

Container Queries

Media Queries

---

# SCSS

Organizar correctamente.

Separar:

Variables

Mixins

Utilities

Components

Layout

Pages

Themes

---

# VARIABLES CSS

Crear variables reutilizables.

Nunca repetir colores.

Ejemplo:

--primary

--secondary

--background

--surface

--text

--border

---

# RESPONSIVE

Toda modificación debe funcionar correctamente en:

HD

Full HD

2K

4K

Ultrawide

Laptop

Tablet

iPad

Android

iPhone

---

# DISEÑO ADAPTATIVO

No simplemente reducir elementos.

Redistribuir completamente.

Ejemplo:

Desktop

4 columnas.

Tablet

2 columnas.

Móvil

1 columna.

---

# ANIMACIONES

Usar únicamente:

Fade

Slide

Scale

Hover

Focus

Ripple

Duración:

200 ms

250 ms

Nunca animaciones excesivas.

---

# ACCESIBILIDAD

Mantener:

Contraste WCAG.

Focus visible.

Labels.

ARIA.

Navegación por teclado.

Objetivos táctiles mayores de 44px.

---

# RENDIMIENTO

No agregar:

Animaciones pesadas.

Librerías innecesarias.

CSS duplicado.

JavaScript innecesario.

Imágenes enormes.

---

# PRINCIPIO DE MODIFICACIÓN

Antes de modificar cualquier archivo debes responder internamente:

¿Qué hace?

¿Quién lo usa?

¿Qué puede romperse?

¿Cómo mejorar la interfaz sin afectar la lógica?

Solo después podrás modificarlo.

---

# REGLA FINAL

Si existe una decisión entre:

"Mejorar el diseño"

o

"Conservar la funcionalidad"

Siempre gana conservar la funcionalidad.

Una interfaz ligeramente menos atractiva es preferible a una interfaz que rompa el funcionamiento del sistema.
# FRONTEND DEVELOPMENT RULES

## Objetivo

Todo cambio realizado debe mejorar la experiencia del usuario sin modificar el comportamiento del sistema.

La prioridad es:

1. Mantener la funcionalidad.
2. Mejorar la organización visual.
3. Mejorar la experiencia del usuario.
4. Mejorar la accesibilidad.
5. Mejorar la consistencia visual.
6. Mantener un rendimiento alto.

---

# HTML

Puedes modificar completamente el HTML siempre que:

- No elimines elementos funcionales.
- No elimines formularios.
- No elimines botones.
- No elimines enlaces.
- No elimines eventos.
- No elimines IDs utilizados por JavaScript.
- No elimines clases utilizadas por JavaScript.
- No elimines atributos data-*.
- No elimines atributos aria.
- No elimines elementos utilizados por Django.

Puedes reorganizar:

- Containers
- Cards
- Sidebar
- Navbar
- Dashboards
- Formularios
- Botones
- Iconos
- Tablas
- Widgets

Todo el HTML puede reorganizarse libremente.

---

# CSS

Todo el CSS puede modernizarse.

Siempre utilizar:

CSS moderno.

Variables.

Flexbox.

Grid.

Clamp.

Minmax.

Auto Fit.

Auto Fill.

Container Queries cuando sea posible.

Media Queries modernas.

Nunca utilizar:

!important innecesarios.

Selectores demasiado específicos.

Código duplicado.

Colores repetidos.

Márgenes excesivos.

Padding inconsistente.

---

# SCSS

Organizar el código.

Separar:

Variables

Mixins

Utilities

Layout

Components

Pages

Animations

Themes

Utilizar nesting únicamente cuando mejore la lectura.

No generar CSS innecesario.

---

# DISEÑO

El diseño debe sentirse como un software premium.

Inspiración:

Apple

Notion

Linear

Stripe

GitHub

Figma

Framer

ClickUp

No copiar.

Solo inspirarse.

---

# SOFT UI

Soft UI será el estilo principal.

Características:

Mucho espacio en blanco.

Interfaces limpias.

Tarjetas suaves.

Sombras discretas.

Bordes redondeados.

Excelente jerarquía visual.

---

# CUPERTINO

Inspirarse en Apple.

Animaciones suaves.

Tipografía limpia.

Navegación clara.

Mucho aire.

Elementos bien alineados.

---

# NEUMORPHISM

Utilizar únicamente como detalle.

Ejemplos:

Botón principal.

Widget destacado.

Dashboard.

Tarjeta principal.

Nunca utilizar en toda la interfaz.

---

# PALETA

Color primario

#F57C00

Color secundario

#0D47A1

Color de error

#D32F2F

Blanco

#FFFFFF

Fondo

#F8F9FB

Fondo secundario

#EEF2F7

Texto

#1F2937

Texto secundario

#6B7280

Bordes

#E5E7EB

---

# TIPOGRAFÍA

Utilizar:

Inter

Si existe:

SF Pro Display.

Jerarquía clara.

Mucho espacio.

Excelente legibilidad.

---

# ESPACIADO

Utilizar sistema de 8 puntos.

8

16

24

32

40

48

64

Nunca colocar elementos demasiado juntos.

---

# TARJETAS

Todas las cards deben verse modernas.

Características:

Mucho padding.

Sombras suaves.

Bordes redondeados.

Hover ligero.

Excelente separación.

---

# BOTONES

Botón primario

Naranja.

Botón secundario

Azul.

Botón peligro

Rojo.

Estados:

Hover

Focus

Disabled

Loading

Pressed

Nunca utilizar botones planos sin jerarquía.

---

# ICONOGRAFÍA

Utilizar una única librería.

Mantener consistencia.

Todos los iconos deben tener el mismo estilo.

---

# FORMULARIOS

Todos los formularios deben modernizarse.

Agrupar información relacionada.

Evitar formularios demasiado largos.

Utilizar varias columnas cuando exista espacio.

Mantener exactamente las mismas validaciones.

---

# INPUTS

Todos los inputs deben tener:

Estado normal.

Hover.

Focus.

Error.

Success.

Disabled.

Readonly.

Nunca modificar la lógica.

---

# TABLAS

Modernizar completamente.

Cabeceras limpias.

Hover elegante.

Filas separadas.

Filtros modernos.

Paginación elegante.

Responsive.

---

# DASHBOARD

Todos los dashboards deben aprovechar el espacio.

Utilizar:

Widgets.

Cards.

Estadísticas.

Accesos rápidos.

Actividad reciente.

Calendarios.

Notificaciones.

---

# SIDEBAR

La sidebar debe ser moderna.

Responsive.

Colapsable.

Iconos consistentes.

Navegación clara.

Excelente jerarquía.

---

# NAVBAR

Navbar limpia.

Minimalista.

Información importante.

Avatar.

Notificaciones.

Buscador.

Breadcrumb.

---

# MODALES

Utilizar modales modernos.

No ocupar toda la pantalla innecesariamente.

Animaciones suaves.

Cerrar fácilmente.

---

# ALERTAS

Las alertas deben ser elegantes.

No bloquear al usuario innecesariamente.

Utilizar colores consistentes.

---

# LOADING

Todos los procesos largos deben mostrar feedback.

Utilizar:

Skeleton.

Spinner.

Progress.

Shimmer.

---

# ESTADOS VACÍOS

Nunca dejar pantallas vacías.

Mostrar:

Ilustración.

Título.

Descripción.

Acción recomendada.

---

# RESPONSIVE

Todo debe ser completamente responsive.

No únicamente adaptable.

Debe aprovechar correctamente cada resolución.

---

# RESOLUCIONES

Optimizar para:

HD

1366x768

Full HD

1920x1080

2K

2560x1440

4K

3840x2160

Ultrawide

21:9

Laptops.

Tablets.

iPad.

Móviles.

---

# COMPORTAMIENTO EN 4K

No simplemente aumentar el tamaño.

Redistribuir.

Mostrar más columnas.

Mostrar más widgets.

Aprovechar el espacio.

---

# COMPORTAMIENTO EN ULTRAWIDE

Evitar enormes espacios vacíos.

Utilizar múltiples paneles.

Distribuir contenido.

---

# MOBILE

No ocultar información importante.

Reorganizar.

Apilar tarjetas.

Utilizar Drawer.

Botones cómodos.

---

# FLEXBOX

Utilizar cuando sea apropiado.

---

# GRID

Preferir Grid para layouts grandes.

---

# CLAMP

Utilizar clamp para:

Fuentes.

Espaciados.

Márgenes.

Botones.

---

# RENDIMIENTO

Todo cambio debe mantener un alto rendimiento.

Evitar:

Animaciones pesadas.

Sombras exageradas.

Filtros excesivos.

JavaScript innecesario.

---

# ACCESIBILIDAD

Contraste adecuado.

Navegación por teclado.

Focus visible.

Etiquetas correctas.

Objetivos táctiles cómodos.

Cumplir WCAG AA.

---

# CONSISTENCIA

Todo el sistema debe sentirse diseñado por una sola persona.

Nunca mezclar estilos.

Nunca utilizar componentes diferentes para la misma función.

Mantener una identidad visual consistente en todas las páginas.

---

# REGLA FINAL

Puedes rediseñar completamente cualquier vista.

Puedes mover cualquier contenedor.

Puedes reorganizar completamente el layout.

Puedes crear una experiencia mucho mejor.

Pero jamás debes modificar la lógica, romper el funcionamiento, eliminar eventos, cambiar validaciones o alterar el comportamiento del sistema.

El usuario debe percibir un sistema completamente nuevo visualmente, mientras que internamente todo debe seguir funcionando exactamente igual.
# PARTE 4 — CALIDAD, RENDIMIENTO, RESPONSIVE Y VALIDACIÓN FINAL

---

# FILOSOFÍA GENERAL

Cada cambio debe mejorar el sistema.

Nunca debe hacerlo más complejo.

Si existen dos soluciones:

- Elegir siempre la más simple.
- Elegir la más mantenible.
- Elegir la más clara.
- Elegir la más consistente.

El usuario final nunca debe notar inconsistencias.

Todo debe sentirse parte del mismo sistema.

---

# CONSISTENCIA VISUAL

Todas las páginas deben compartir el mismo lenguaje visual.

Nunca diseñar una página con un estilo diferente.

Mantener consistencia en:

- Espaciados
- Bordes
- Sombras
- Colores
- Tipografía
- Iconografía
- Botones
- Formularios
- Tablas
- Cards
- Modales
- Menús
- Navegación

Si un componente existe en varias páginas debe verse exactamente igual.

---

# NO DUPLICAR COMPONENTES

Si ya existe un estilo para un botón:

usar ese estilo.

Si ya existe una tarjeta:

reutilizarla.

Si ya existe un modal:

mantener el mismo diseño.

No crear variantes innecesarias.

---

# JERARQUÍA VISUAL

Toda página debe responder visualmente:

1.

¿Qué es lo más importante?

2.

¿Qué acción debe realizar el usuario?

3.

¿Qué información debe leer después?

4.

¿Qué acciones secundarias existen?

Nunca colocar demasiados elementos con el mismo peso visual.

---

# ESPACIADO

Usar sistema de 8px.

8

16

24

32

40

48

64

Nunca colocar elementos demasiado juntos.

Nunca desperdiciar espacio.

---

# ALINEACIÓN

Todo debe alinearse correctamente.

Evitar:

alineaciones aleatorias

padding diferentes

márgenes diferentes

anchos inconsistentes

---

# BOTONES

Botón principal

Siempre destacar.

Botón secundario

Menor protagonismo.

Botón peligro

Solo para acciones destructivas.

No utilizar demasiados colores.

---

# ICONOS

Usar una sola familia.

Todos deben tener:

mismo tamaño

mismo grosor

mismo estilo

No mezclar estilos.

---

# TARJETAS

Las cards deben tener:

espaciado amplio

bordes suaves

sombras discretas

buena separación

Nunca saturarlas.

---

# TABLAS

Las tablas deben ser:

claras

ordenadas

fáciles de leer

hover suave

cabeceras visibles

responsive

Si una tabla es demasiado grande:

adaptarla.

No romper el diseño.

---

# FORMULARIOS

Todos los formularios deben:

verse iguales

mantener la misma separación

tener ayudas claras

mostrar errores correctamente

No cambiar validaciones.

---

# MENSAJES

Los mensajes deben ser:

claros

cortos

profesionales

Nunca mostrar errores técnicos al usuario.

---

# RESPONSIVE

Cada página debe verse correctamente en:

HD

1366

Full HD

1920

QHD

2560

4K

3840

Ultrawide

Laptop

Tablet

iPad

Android

iPhone

---

# COMPORTAMIENTO RESPONSIVE

Desktop

Sidebar fija

Dashboard grande

Varias columnas

Mucho espacio

---

Laptop

Reducir columnas.

Mantener comodidad.

---

Tablet

Sidebar colapsable.

Cards grandes.

Dos columnas.

---

Móvil

Una columna.

Drawer.

Botones completos.

Cards verticales.

---

# EN 4K

Nunca simplemente estirar.

Reorganizar.

Agregar columnas.

Mejor distribución.

Más información útil.

No enormes espacios vacíos.

---

# ULTRAWIDE

Usar múltiples columnas.

Mantener lectura cómoda.

No dejar el contenido pequeño en el centro.

---

# ESCALADO

Escalar automáticamente:

fuentes

botones

cards

tablas

formularios

widgets

gráficas

iconos

padding

margin

---

# CSS

Preferir:

Grid

Flexbox

Gap

Clamp

Minmax

Auto-fit

Auto-fill

Container Queries

Media Queries

REM

EM

---

# EVITAR

Width fijos.

Height fijos.

Overflow.

Scroll horizontal.

Posiciones absolutas innecesarias.

CSS repetido.

!important.

Selectores demasiado largos.

---

# RENDIMIENTO

No agregar:

JavaScript innecesario.

CSS innecesario.

Bibliotecas innecesarias.

Dependencias innecesarias.

---

# CSS

Reducir:

duplicación

reglas innecesarias

selectores complejos

anidaciones profundas

---

# HTML

Mantener limpio.

Semántico.

Fácil de leer.

Ordenado.

---

# JAVASCRIPT

No modificar comportamiento.

No crear lógica innecesaria.

No duplicar eventos.

---

# ACCESIBILIDAD

Cumplir WCAG AA.

Mantener:

contraste

focus

tabulación

labels

aria cuando sea necesario

botones accesibles

objetivos táctiles mínimos de 44x44 px

---

# UX

Cada pantalla debe responder:

¿Qué quiere hacer el usuario?

¿Dónde debe hacer clic?

¿Cómo regresar?

¿Cómo cancelar?

¿Cómo confirmar?

---

# MICROINTERACCIONES

Agregar únicamente cuando aporten valor.

Hover

Focus

Pressed

Loading

Success

Nunca exagerar.

---

# LOADING

Utilizar:

Skeleton

Placeholder

Fade

Nunca dejar pantallas completamente vacías.

---

# ESTADOS VACÍOS

Cuando no existan datos:

Mostrar ilustración simple.

Mensaje claro.

Acción recomendada.

---

# ERRORES

Mostrar mensajes claros.

Explicar qué ocurrió.

Indicar cómo solucionarlo.

Nunca mostrar errores técnicos.

---

# ÉXITO

Mostrar confirmaciones discretas.

No interrumpir al usuario.

---

# MODALES

Utilizar únicamente cuando sean necesarios.

No abusar.

Permitir cerrar fácilmente.

---

# DASHBOARD

Debe mostrar únicamente información útil.

No llenar de widgets innecesarios.

---

# DISEÑO

Inspirarse en:

Apple

Stripe

Linear

GitHub

Notion

Vercel

Figma

ClickUp

Sin copiar.

---

# ANTES DE MODIFICAR UN ARCHIVO

Leer completamente.

Comprenderlo.

Identificar dependencias.

Identificar eventos.

Identificar formularios.

Identificar JavaScript.

Solo después modificar.

---

# DESPUÉS DE MODIFICAR

Revisar:

Responsive.

Consistencia.

Espaciados.

Sombras.

Contraste.

Accesibilidad.

Funcionamiento.

---

# CHECKLIST FINAL

Antes de considerar terminado cualquier cambio verificar:

✓ No cambió la lógica.

✓ No cambió ninguna función.

✓ No cambió ninguna consulta.

✓ No cambió ningún endpoint.

✓ No cambió ningún modelo.

✓ No cambió ninguna URL.

✓ No cambió autenticación.

✓ No cambió permisos.

✓ No cambió validaciones.

✓ No cambió JavaScript funcional.

✓ No eliminó eventos.

✓ No eliminó IDs.

✓ No eliminó atributos utilizados por scripts.

✓ No eliminó Template Tags.

✓ No eliminó csrf_token.

✓ No rompió HTMX.

✓ No rompió Alpine.

✓ No rompió AJAX.

✓ No rompió formularios.

✓ Todo continúa funcionando.

✓ Todas las páginas son responsive.

✓ Funciona correctamente en HD.

✓ Funciona correctamente en Full HD.

✓ Funciona correctamente en 2K.

✓ Funciona correctamente en 4K.

✓ Funciona correctamente en Ultrawide.

✓ Funciona correctamente en Laptop.

✓ Funciona correctamente en Tablet.

✓ Funciona correctamente en iPad.

✓ Funciona correctamente en móviles.

✓ Mantiene la misma lógica.

✓ Mantiene el mismo comportamiento.

✓ Mantiene el mismo flujo.

✓ El único cambio realizado fue mejorar el diseño y la experiencia de usuario.

---

# OBJETIVO FINAL

Cada modificación debe hacer que el proyecto se vea como un software SaaS profesional de 2026.

Debe sentirse:

Elegante.

Moderno.

Limpio.

Profesional.

Rápido.

Consistente.

Accesible.

Escalable.

Responsivo.

Sin modificar la lógica del sistema.

La prioridad absoluta siempre será:

1. Mantener la funcionalidad.
2. Mejorar la experiencia de usuario.
3. Mejorar la calidad visual.
4. Mantener un código limpio y mantenible.
# UI_GUIDELINES.md

# Capítulo 1
# Filosofía de Diseño y Principios Generales

---

# Objetivo

Este documento define el sistema de diseño oficial del proyecto.

Todas las interfaces nuevas y existentes deberán seguir estas reglas para garantizar consistencia visual, excelente experiencia de usuario y una identidad moderna.

La aplicación debe sentirse como un software SaaS profesional desarrollado entre 2026 y 2030.

No se deben crear vistas con estilos diferentes entre sí.

Todo debe parecer parte del mismo ecosistema.

---

# Filosofía del Diseño

La aplicación debe transmitir:

- Profesionalismo
- Claridad
- Simplicidad
- Elegancia
- Rapidez
- Confianza
- Productividad

Cada elemento debe tener un propósito.

Nunca agregar elementos únicamente por decoración.

Cada componente debe ayudar al usuario.

---

# Identidad Visual

La identidad del sistema está basada en tres estilos.

## Soft UI (70%)

Es el estilo principal.

Debe dominar toda la aplicación.

Características:

- Mucho espacio en blanco
- Sombras suaves
- Interfaces limpias
- Tarjetas flotantes
- Bordes redondeados
- Jerarquía clara
- Diseño relajado
- Excelente legibilidad

Evitar:

- Interfaces saturadas
- Colores muy agresivos
- Sombras exageradas
- Exceso de información

---

## Cupertino (20%)

Inspirado en Apple.

No copiar el diseño de Apple.

Tomar únicamente inspiración.

Aplicar:

- Navegación elegante

- Espaciados amplios

- Interfaces cómodas

- Animaciones suaves

- Mucha limpieza visual

- Componentes minimalistas

- Excelente organización

La aplicación debe sentirse cómoda para utilizar durante varias horas.

---

## Neumorphism Ligero (10%)

Solo utilizar como detalle.

Nunca utilizar como estilo principal.

Aplicarlo únicamente en:

- Botón principal

- Tarjetas importantes

- Widgets

- Dashboard

- Accesos rápidos

No utilizar en:

- Todos los formularios

- Todas las tarjetas

- Tablas

- Sidebar

- Navbar

Debe utilizarse únicamente para destacar información importante.

---

# Principios UX

Todo el sistema debe seguir los siguientes principios.

## 1. Menos es más

No agregar elementos innecesarios.

Cada componente debe tener un propósito.

Eliminar ruido visual.

---

## 2. Priorizar el contenido

El usuario entra al sistema para trabajar.

No para admirar el diseño.

El contenido siempre debe ser el protagonista.

---

## 3. Consistencia

Todas las vistas deben compartir:

- Colores

- Espaciados

- Bordes

- Tipografía

- Botones

- Formularios

- Tablas

- Iconografía

Nunca diseñar una página completamente diferente de otra.

---

## 4. Claridad

Toda acción importante debe ser evidente.

El usuario nunca debe preguntarse:

"¿Dónde doy clic?"

Los botones importantes deben destacar.

Las acciones secundarias deben permanecer discretas.

---

## 5. Jerarquía Visual

Todo elemento debe tener un nivel de importancia.

Ejemplo:

Título

↓

Subtítulo

↓

Contenido

↓

Acciones

↓

Información secundaria

Nunca mostrar todos los elementos con el mismo peso visual.

---

## 6. Espacio en Blanco

El espacio en blanco es parte del diseño.

No llenar todas las áreas disponibles.

Una interfaz limpia transmite profesionalismo.

---

# Sensación General

La aplicación debe sentirse:

✓ moderna

✓ rápida

✓ ligera

✓ profesional

✓ elegante

✓ premium

✓ intuitiva

Nunca debe sentirse:

✗ pesada

✗ saturada

✗ antigua

✗ improvisada

✗ escolar

✗ desordenada

---

# Experiencia del Usuario

El usuario debe entender la interfaz sin necesidad de capacitación.

Cada pantalla debe responder tres preguntas en menos de cinco segundos:

1.

¿Dónde estoy?

2.

¿Qué puedo hacer aquí?

3.

¿Cuál es la siguiente acción?

Si alguna respuesta no es evidente, el diseño debe mejorarse.

---

# Uso del Color

El color nunca debe utilizarse únicamente por estética.

Debe comunicar.

Ejemplos:

Naranja

↓

Acción principal

Azul Marino

↓

Navegación

Rojo

↓

Error

Eliminar

Advertencia

Verde

↓

Éxito

Confirmación

Información positiva

No utilizar colores aleatorios.

Todo color debe tener una función.

---

# Equilibrio Visual

Cada pantalla debe sentirse equilibrada.

Evitar:

Muchos botones juntos.

Muchos colores diferentes.

Muchas tarjetas.

Muchos iconos.

Muchos textos largos.

Buscar siempre un balance entre contenido y espacio libre.

---

# Diseño Atemporal

No seguir modas pasajeras.

El diseño debe seguir viéndose moderno durante varios años.

Evitar tendencias exageradas.

Priorizar:

Minimalismo.

Legibilidad.

Consistencia.

Elegancia.

---

# Calidad Visual

Cada pantalla debe parecer diseñada por un equipo profesional.

Antes de considerar terminada una vista preguntarse:

¿Se siente profesional?

¿Es cómoda de utilizar?

¿Existe suficiente espacio?

¿La información está organizada?

¿Hay demasiados elementos?

¿Podría simplificarse aún más?

---

# Inspiración

Tomar inspiración en plataformas como:

Apple

Notion

Linear

GitHub

Stripe

Figma

Vercel

Craft

ClickUp

Microsoft 365

Google Workspace

Canvas LMS

No copiar diseños.

Inspirarse únicamente en:

- Organización

- Espaciados

- Navegación

- Jerarquía

- Experiencia de usuario

- Claridad

---

# Regla Fundamental

Siempre priorizar:

Experiencia de usuario

↓

Claridad

↓

Funcionalidad

↓

Consistencia

↓

Belleza

Nunca sacrificar la usabilidad únicamente para lograr un diseño llamativo.

Una interfaz bonita pero difícil de usar es un mal diseño.

Una interfaz elegante, clara y rápida siempre será la mejor opción.

---
# 2. Sistema de Diseño (Design System)

## Objetivo

Todo el proyecto debe seguir un único sistema de diseño consistente.

No crear componentes con estilos aislados.

Todos los colores, tamaños, márgenes, tipografías, radios y sombras deben provenir del sistema de diseño.

El objetivo es que cualquier pantalla parezca parte del mismo producto.

---

# Design Tokens

Todos los valores visuales deben definirse mediante variables reutilizables.

Nunca escribir colores o tamaños directamente dentro de los componentes cuando puedan reutilizarse.

Utilizar variables CSS o SCSS.

Ejemplo:

```css
:root{

--primary:#F57C00;
--secondary:#0D47A1;
--danger:#D32F2F;

--background:#F8F9FB;
--surface:#FFFFFF;

--text:#1F2937;
--text-secondary:#6B7280;

--success:#22C55E;
--warning:#F59E0B;

--border:#E5E7EB;

}
```

---

# Paleta de colores

La aplicación debe transmitir:

Profesionalismo

Elegancia

Tecnología

Educación

Claridad

Modernidad

Nunca debe sentirse infantil.

---

## Color Primario

Naranja

#F57C00

Uso:

Botones principales

FAB

Acciones importantes

Links destacados

Indicadores activos

Gráficas principales

---

## Color Secundario

Azul Marino

#0D47A1

Uso:

Sidebar

Navbar

Headers

Títulos importantes

Filtros activos

Botones secundarios

---

## Color de Error

Rojo

#D32F2F

Uso:

Eliminar

Errores

Advertencias críticas

Alertas

No utilizarlo como color principal.

---

## Éxito

Verde

#22C55E

Uso:

Guardado exitoso

Estados completados

Confirmaciones

Indicadores positivos

---

## Advertencia

Amarillo

#F59E0B

Uso:

Avisos

Información importante

Pendientes

---

## Fondo principal

#F8F9FB

Debe ocupar casi toda la aplicación.

Nunca utilizar fondos oscuros salvo que exista Dark Mode.

---

## Fondo secundario

#EEF2F7

Utilizar para:

Dashboard

Widgets

Cards destacadas

Secciones

---

## Superficies

Blanco

#FFFFFF

Utilizar para:

Cards

Formularios

Inputs

Modales

Dropdowns

Tablas

---

## Texto

Principal

#1F2937

Debe tener excelente contraste.

---

Texto secundario

#6B7280

Utilizar para:

Descripción

Información secundaria

Fechas

Ayuda

Nunca utilizar gris demasiado claro.

---

## Bordes

#E5E7EB

Los bordes deben ser muy discretos.

Nunca negros.

---

# Gradientes

Los gradientes deben ser muy sutiles.

Ejemplo:

Naranja

#F57C00

↓

#FB923C

---

Azul

#0D47A1

↓

#2563EB

---

No abusar de gradientes.

---

# Sombras

Las sombras deben ser suaves.

Ejemplo

```css
box-shadow:

0 10px 30px rgba(15,23,42,.08);
```

Nunca utilizar sombras negras fuertes.

---

# Tipografía

Utilizar:

Inter

Si existe:

SF Pro Display

---

Nunca mezclar múltiples familias tipográficas.

---

Jerarquía

H1

32px

Peso 700

---

H2

28px

Peso 700

---

H3

24px

Peso 600

---

H4

20px

Peso 600

---

Texto principal

16px

Peso 400

---

Texto secundario

15px

Peso 400

---

Ayuda

14px

Peso 400

---

Caption

13px

Peso 400

---

Botones

16px

Peso 600

---

Nunca utilizar fuentes menores de 13px.

---

# Altura de línea

Títulos

120%

Texto

150%

Listas

160%

---

# Espaciado

Utilizar un sistema basado en múltiplos de 8.

Espaciados permitidos

4

8

12

16

24

32

40

48

56

64

80

96

---

Nunca utilizar valores aleatorios.

Incorrecto

17px

23px

31px

Correcto

16px

24px

32px

64px

---

# Márgenes

Entre componentes

24px

Entre secciones

48px

Entre tarjetas

24px

Entre formularios

32px

---

# Padding

Cards

24px

Widgets

24px

Inputs

16px

Botones

16px horizontal

12px vertical

---

# Bordes redondeados

Botones

16px

Inputs

16px

Cards

24px

Dashboard

24px

Modales

28px

Badges

999px

---

# Iconografía

Utilizar un solo sistema de iconos.

Preferentemente

Material Symbols

o

Font Awesome

o

Heroicons

Nunca mezclar librerías.

---

Los iconos deben tener:

20px

24px

28px

32px

No utilizar tamaños aleatorios.

---

# Estados

Todos los componentes deben tener:

Normal

Hover

Focus

Active

Disabled

Loading

Success

Error

---

Los estados deben ser consistentes en toda la aplicación.

---

# Elevación

Nivel 0

Sin sombra

---

Nivel 1

Cards normales

---

Nivel 2

Dropdown

Popover

---

Nivel 3

Modales

---

Nivel 4

Toast

Dialogs

---

Nunca utilizar elevaciones exageradas.

---

# Principios visuales

La aplicación debe sentirse:

Ligera

Limpia

Profesional

Moderna

Rápida

Minimalista

Elegante

Nunca:

Recargada

Infantil

Colorida en exceso

Con sombras exageradas

Con bordes negros

Con demasiados efectos

---

# Regla de consistencia

Antes de crear cualquier componente preguntar:

¿Respeta la paleta?

¿Respeta el sistema de espaciado?

¿Respeta la tipografía?

¿Respeta el radio?

¿Respeta la elevación?

¿Respeta el estilo general?

Si la respuesta es NO, debe corregirse antes de continuar.
# 3. Tipografía y Sistema de Espaciado

---

# Objetivo

La tipografía y el espaciado son responsables de la mayor parte de la percepción de calidad de una interfaz.

El objetivo es construir una interfaz limpia, moderna, consistente y fácil de leer durante largas sesiones de trabajo.

La aplicación debe sentirse como un software SaaS premium de 2026.

Nunca diseñar interfaces saturadas.

La claridad siempre tiene prioridad sobre los efectos visuales.

---

# Principios

Cada pantalla debe cumplir estas reglas.

✓ Mucho espacio en blanco.

✓ Jerarquía visual clara.

✓ Lectura cómoda.

✓ Excelente alineación.

✓ Espaciados consistentes.

✓ Distribución equilibrada.

✓ Componentes respirando entre sí.

Nunca colocar elementos demasiado juntos.

Nunca saturar una pantalla con demasiada información.

---

# Tipografía

Fuente principal

Inter

Alternativas

SF Pro Display

Segoe UI

Roboto

Solo utilizar una familia tipográfica en toda la aplicación.

No mezclar fuentes.

---

# Pesos

Light

300

Regular

400

Medium

500

SemiBold

600

Bold

700

Evitar pesos superiores.

---

# Jerarquía

## Display

48px

Peso 700

Uso

Landing

Login

Pantallas principales

---

## Título Principal

36px

Peso 700

Uso

Dashboard

Módulos

Configuraciones

---

## Título Secundario

30px

Peso 600

Uso

Secciones

---

## Heading

26px

Peso 600

Uso

Cards

Widgets

---

## Subtítulo

22px

Peso 600

---

## Texto grande

18px

Peso 500

---

## Texto normal

16px

Peso 400

Este será el tamaño utilizado en casi toda la aplicación.

---

## Texto pequeño

14px

Peso 400

Uso

Ayudas

Descripciones

Notas

---

## Texto auxiliar

12px

Uso

Etiquetas secundarias

Información de apoyo

Nunca utilizar menos de 12px.

---

# Altura de línea

Display

1.2

Títulos

1.3

Texto

1.6

Descripción

1.8

Esto mejora muchísimo la lectura.

---

# Espaciado entre letras

Display

-1px

Títulos

-0.5px

Texto

0

Nunca exagerar el tracking.

---

# Colores del texto

Principal

#1F2937

Secundario

#6B7280

Placeholder

#9CA3AF

Deshabilitado

#CBD5E1

Links

Color primario.

---

# Longitud del texto

Evitar líneas extremadamente largas.

Ideal

60–80 caracteres por línea.

---

# Alineación

Títulos

Izquierda.

Texto

Izquierda.

Nunca justificar.

---

# Sistema de Espaciado

Utilizar un sistema basado en múltiplos de 8.

Nunca inventar medidas aleatorias.

Utilizar únicamente:

4

8

12

16

20

24

32

40

48

56

64

72

80

96

128

---

# Padding

Cards

24px

Dashboard

32px

Modales

32px

Sidebar

24px

Navbar

20px

Botones

16px horizontal

12px vertical

Inputs

16px

Tablas

16px

Widgets

24px

---

# Márgenes

Título → Subtítulo

8px

Título → Contenido

24px

Card → Card

24px

Formulario → Formulario

32px

Input → Input

20px

Sección → Sección

48px

Página → Página

64px

---

# Grid

Usar CSS Grid preferentemente.

Ejemplo

Desktop

4 columnas

Laptop

3 columnas

Tablet

2 columnas

Móvil

1 columna

Nunca dejar grandes espacios vacíos.

---

# Anchos máximos

Contenido principal

1400px

Formularios

900px

Login

500px

Dashboard

1600px

Tablas

100%

Nunca utilizar contenido de 100% cuando reduzca la legibilidad.

---

# Altura mínima

Las tarjetas deben tener una altura coherente.

Evitar tarjetas extremadamente pequeñas.

---

# Espacio entre iconos y texto

8px

Nunca pegar iconos al texto.

---

# Botones

Altura mínima

44px

Ideal

48px

Padding

16px

Radio

18px

Icono

20px

Separación icono-texto

8px

---

# Inputs

Altura

48px

Padding

16px

Radio

16px

Label superior

Siempre que sea posible.

---

# Cards

Padding

24px

Radio

22px

Espacio interno amplio.

---

# Dashboard

Separación entre widgets

24px

Separación entre filas

32px

Widgets grandes.

No saturar.

---

# Sidebar

Ancho recomendado

280px

Iconos

22px

Separación vertical

12px

Padding

24px

---

# Navbar

Altura

72px

Padding

24px

Elementos alineados verticalmente.

---

# Tablas

Padding

16px

Altura de fila

56px

Hover suave.

Cabecera diferenciada.

---

# Formularios

Agrupar campos relacionados.

No crear formularios excesivamente largos.

Dividir en secciones.

Usar múltiples columnas cuando el espacio lo permita.

---

# Espacio en blanco

Una buena interfaz utiliza el espacio vacío como herramienta de organización.

Nunca intentar llenar toda la pantalla.

El espacio vacío mejora:

• Comprensión.

• Jerarquía.

• Accesibilidad.

• Experiencia de usuario.

---

# Responsive Tipográfico

Desktop

Display 48px

Título 36px

Texto 16px

Tablet

Display 40px

Título 30px

Texto 16px

Móvil

Display 32px

Título 24px

Texto 16px

Nunca reducir el texto principal por debajo de 16px.

---

# Reglas Generales

Siempre utilizar rem en lugar de px cuando sea posible.

Utilizar clamp() para tamaños fluidos.

Ejemplo

font-size: clamp(1rem, 1vw + 0.5rem, 2rem);

No utilizar tamaños fijos innecesarios.

Mantener una escala tipográfica consistente en todo el proyecto.

Cada página debe sentirse parte del mismo sistema de diseño.

Si una decisión mejora la claridad, la accesibilidad y la experiencia de usuario, debe preferirse aunque implique reorganizar visualmente la interfaz, siempre sin modificar la lógica del sistema.
# Layout & Grid System

## Filosofía

El layout debe priorizar la claridad, la productividad y el aprovechamiento inteligente del espacio disponible.

Nunca diseñar pensando únicamente en una resolución.

Cada vista debe reorganizarse automáticamente según el tamaño de la pantalla.

El usuario debe sentir que la interfaz fue diseñada específicamente para su dispositivo.

---

# Principios

Priorizar:

✓ Claridad

✓ Simplicidad

✓ Consistencia

✓ Escalabilidad

✓ Productividad

✓ Rapidez visual

✓ Mucho espacio en blanco

Evitar:

✗ Interfaces saturadas

✗ Componentes demasiado juntos

✗ Contenedores gigantes

✗ Espacios muertos excesivos

✗ Scroll horizontal

✗ Layouts rígidos

---

# Sistema de Grid

Utilizar CSS Grid como primera opción.

Utilizar Flexbox cuando sea más conveniente.

Evitar layouts construidos únicamente con márgenes.

---

# Distribución

Dashboard

Desktop

4-6 columnas

Tablet

2-3 columnas

Móvil

1 columna

---

Formularios

Desktop

3-4 columnas cuando exista espacio.

Laptop

2-3 columnas.

Tablet

2 columnas.

Móvil

1 columna.

---

Cards

Las tarjetas deben tener siempre el mismo alto cuando pertenezcan a un mismo grupo.

Nunca dejar tarjetas desalineadas.

Utilizar:

align-items: stretch;

---

Sidebar

Desktop

Fija.

Colapsable.

Tablet

Colapsable.

Móvil

Drawer.

Nunca ocupar toda la pantalla cuando no sea necesario.

---

Navbar

Debe mantenerse limpia.

Máximo tres niveles visuales.

No sobrecargar.

---

Contenedores

Utilizar max-width cuando sea necesario.

No permitir líneas extremadamente largas.

Recomendado:

1200px

1400px

1600px

dependiendo del contenido.

---

Espaciado

Sistema de 8 puntos.

Utilizar múltiplos de:

4

8

16

24

32

40

48

64

Nunca utilizar valores aleatorios.

---

Jerarquía

Cada página debe tener claramente:

Título

Descripción

Acciones principales

Contenido

Información secundaria

Acciones flotantes

---

Alineación

Todo debe alinearse mediante Grid.

Evitar márgenes negativos.

Evitar posicionamientos absolutos innecesarios.

---

Cards

Preferir:

Grid

Auto Fit

Auto Fill

Ejemplo conceptual

repeat(auto-fit,minmax(320px,1fr))

---

Espacios

Mucho aire.

No llenar la pantalla únicamente porque existe espacio disponible.

El espacio también comunica.

---

Modales

Centrados.

Máximo 70% del ancho.

Responsive.

No ocupar toda la pantalla salvo cuando sea indispensable.

---

Dashboards

Los widgets deben reorganizarse automáticamente.

Nunca quedar una sola tarjeta enorme mientras otras son pequeñas.

Mantener proporciones.

---

Tablas

No obligar al usuario a hacer zoom.

Si la información no cabe:

Convertir parcialmente en Cards.

Agregar scroll horizontal únicamente como último recurso.

---

Principio General

Cada pantalla debe sentirse diseñada específicamente para su resolución.
# 6. COMPONENTES

## Objetivo

Todos los componentes del sistema deben compartir un mismo lenguaje visual.

El usuario debe sentir que toda la plataforma pertenece al mismo producto.

No debe haber componentes con estilos diferentes entre módulos.

Todos los componentes deben seguir el Design System.

---

# Principios

Cada componente debe ser:

- Claro
- Consistente
- Fácil de identificar
- Fácil de utilizar
- Accesible
- Responsive
- Reutilizable

Nunca diseñar un componente únicamente para una página.

Debe poder reutilizarse en cualquier parte del sistema.

---

# Bordes

Utilizar bordes suaves.

Componentes pequeños

12px

Inputs

16px

Botones

16px

Cards

22px

Modales

24px

Nunca utilizar bordes cuadrados.

---

# Sombras

Sombras muy suaves.

No exagerar profundidad.

Ejemplo

Shadow XS

0 2px 8px rgba(15,23,42,.05)

Shadow S

0 6px 18px rgba(15,23,42,.06)

Shadow M

0 12px 30px rgba(15,23,42,.08)

Shadow L

0 18px 45px rgba(15,23,42,.10)

Nunca utilizar sombras negras intensas.

---

# Botones

Los botones son uno de los elementos más importantes del sistema.

Deben ser consistentes.

Tamaño mínimo

44px de alto.

Radio

16px

Padding horizontal amplio.

Nunca crear botones pequeños difíciles de presionar.

---

## Botón Primario

Color naranja.

Debe llamar la atención.

Se utiliza únicamente para la acción principal.

Ejemplos

Guardar

Crear

Aceptar

Enviar

Continuar

No utilizar más de un botón primario dominante por sección.

---

## Botón Secundario

Azul marino.

Para acciones secundarias.

Ejemplos

Editar

Ver detalles

Actualizar

---

## Botón Terciario

Solo texto.

Sin fondo.

Para acciones poco importantes.

---

## Botón Destructivo

Rojo.

Eliminar.

Cancelar procesos.

Cerrar sesión.

Debe solicitar confirmación cuando la acción sea irreversible.

---

## Estados

Cada botón debe tener

Normal

Hover

Pressed

Focus

Disabled

Loading

---

# Inputs

Los formularios deben transmitir claridad.

Nunca colocar demasiados campos juntos.

Agrupar información relacionada.

---

Cada Input debe tener

Label

Placeholder

Ayuda

Mensaje de error

Mensaje de éxito

Icono cuando aporte valor.

---

Focus

El usuario debe identificar inmediatamente cuál campo está editando.

Utilizar

Borde naranja.

Sombra ligera.

Nunca utilizar outlines feos del navegador.

---

Errores

Utilizar rojo únicamente para errores.

Nunca pintar todo el formulario de rojo.

Mostrar mensajes claros.

---

# Selects

Los Select deben verse iguales que los Inputs.

No utilizar estilos del navegador.

Mostrar icono desplegable moderno.

---

# Textareas

Altura mínima

120px.

Auto Resize cuando sea posible.

---

# Checkbox

Grandes.

Fáciles de presionar.

Estados claros.

---

# Radio Buttons

Separación suficiente.

No demasiado pequeños.

---

# Switches

Inspirados en iOS.

Movimiento suave.

---

# Cards

Las Cards son el componente principal del sistema.

Utilizar:

Mucho padding.

Mucho espacio.

Título claro.

Subtítulo.

Contenido.

Acciones.

Nunca saturar una Card.

---

# Listas

Separación amplia.

Hover ligero.

Bordes suaves.

Scroll agradable.

---

# Tablas

Diseño moderno.

Cabecera fija cuando sea posible.

Hover.

Ordenamiento.

Filtros.

Paginación.

Responsive.

En móviles convertir a tarjetas cuando tenga sentido.

---

# Modales

Nunca ocupar toda la pantalla en Desktop.

Centrados.

Animación Fade + Scale.

Radio

24px

Mucho espacio interno.

---

# Tooltips

Información breve.

Nunca utilizar Tooltips para información importante.

---

# Dropdowns

Animación Fade.

Mucho espacio.

No saturar opciones.

---

# Badges

Pequeños.

Colores suaves.

No utilizar colores muy fuertes.

---

# Alertas

Éxito

Verde

Advertencia

Amarillo

Información

Azul

Error

Rojo

Siempre incluir icono.

---

# Skeleton Loading

Nunca mostrar pantallas vacías.

Utilizar Skeletons.

Animación Shimmer.

---

# Estados Vacíos

Cada módulo debe tener una pantalla vacía.

Debe incluir

Icono

Título

Descripción

Botón principal

---

# Iconografía

Utilizar únicamente una familia.

Preferentemente

Font Awesome

Bootstrap Icons

Heroicons

Material Symbols

Nunca mezclar varias librerías.

---

# Microinteracciones

Hover

Scale

Fade

Ripple

Focus

Duración

200ms

Nunca utilizar animaciones largas.

---

# Consistencia

Todos los componentes deben compartir:

Mismo radio

Misma sombra

Misma tipografía

Mismo padding

Misma animación

Mismos colores

Mismo comportamiento

Nunca crear componentes visualmente diferentes para resolver el mismo problema.
# 8. TABLAS (DATA TABLES)

## Objetivo

Las tablas deben ser modernas, fáciles de leer, altamente responsivas y optimizadas para grandes cantidades de información.

Nunca deben sentirse pesadas o difíciles de utilizar.

Las tablas deben priorizar:

- Legibilidad
- Escaneo rápido
- Accesibilidad
- Productividad
- Excelente uso del espacio

---

# Filosofía

Las tablas no deben parecer hojas de Excel.

Deben parecer interfaces SaaS modernas similares a:

- Stripe
- Linear
- Notion
- GitHub
- Vercel
- Supabase Dashboard

---

# Diseño

Utilizar tarjetas (Cards) como contenedor.

Nunca colocar una tabla directamente sobre el fondo.

Ejemplo:

┌─────────────────────────────────────┐
│ Usuarios                            │
│-------------------------------------│
│ Buscar...             [+ Nuevo]     │
│-------------------------------------│
│ Tabla                               │
│                                     │
│                                     │
└─────────────────────────────────────┘

---

# Encabezados

Los encabezados deben:

- tener fondo ligeramente diferente
- ser sticky cuando sea posible
- texto semibold
- icono de ordenamiento
- padding amplio

No utilizar bordes negros.

---

# Filas

Cada fila debe tener:

- altura cómoda
- hover suave
- transición de 200ms
- separación visual

No utilizar líneas negras entre filas.

Preferir espacios y sombras suaves.

---

# Hover

El hover debe:

- cambiar ligeramente el fondo
- mostrar acciones rápidas
- mantener excelente contraste

Nunca usar colores agresivos.

---

# Selección

Cuando una fila sea seleccionada:

- borde izquierdo con color primario
- fondo ligeramente resaltado

Nunca usar colores fuertes.

---

# Acciones

Las acciones deben agruparse.

Preferir:

Editar

Ver

Eliminar

Más opciones (...)

Utilizar iconos antes que texto cuando sea claro.

---

# Columnas

Evitar columnas demasiado estrechas.

Permitir:

- auto ajuste
- ancho flexible

No fijar anchos innecesarios.

---

# Responsive

Desktop

Mostrar tabla completa.

Laptop

Reducir columnas secundarias.

Tablet

Ocultar información menos importante.

Móvil

Transformar automáticamente la tabla en tarjetas.

Nunca generar scroll horizontal si existe una mejor alternativa.

---

# Paginación

Utilizar una paginación moderna.

Mostrar:

Anterior

Siguiente

Página actual

Total de registros

Filas por página

---

# Estados Vacíos

Cuando no existan registros:

Mostrar una ilustración.

Título.

Descripción.

Botón principal.

Ejemplo:

No hay alumnos registrados.

Registrar alumno.

Nunca dejar una tabla vacía.

---

# Búsqueda

Siempre colocar buscador.

Preferentemente arriba a la izquierda.

Con icono.

Placeholder claro.

---

# Filtros

Los filtros deben estar visibles.

Utilizar:

Dropdown

Chips

Select

Fecha

Nunca esconderlos en menús complicados.

---

# Ordenamiento

Cada columna importante debe poder ordenarse.

Mostrar:

▲

▼

Al pasar el cursor.

---

# Colores

Utilizar:

Fondo

#FFFFFF

Header

#F8F9FB

Hover

#F3F6FA

Texto

#1F2937

Borde

#E5E7EB

---

# Sombras

Muy suaves.

Nunca exageradas.

---

# Animaciones

Fade

Hover

Scale ligero

200ms

---

# Accesibilidad

Contraste WCAG AA.

Tamaño mínimo de texto:

14px

Altura mínima de fila:

48px

Objetivos táctiles:

44px

---

# Buenas prácticas

No usar tablas para móviles.

No usar demasiadas columnas.

No usar bordes negros.

No saturar de información.

Utilizar espacios.

Mantener excelente jerarquía visual.

=====================================================================

# 9. FORMULARIOS

## Objetivo

Los formularios deben ser rápidos, intuitivos y agradables de utilizar.

La prioridad es reducir la carga cognitiva del usuario.

El usuario debe entender inmediatamente qué información necesita proporcionar.

---

# Inspiración

Apple

Notion

Linear

Stripe

Framer

Supabase

GitHub

---

# Organización

Agrupar los campos relacionados.

Utilizar tarjetas.

Separar visualmente cada sección.

Ejemplo:

Información General

Información Personal

Dirección

Datos Escolares

Configuración

---

# Distribución

Desktop

2 a 4 columnas.

Laptop

2 columnas.

Tablet

2 columnas.

Móvil

1 columna.

Nunca utilizar una sola columna en Desktop si existe espacio.

---

# Inputs

Todos los inputs deben tener:

Radio:

16px

Padding amplio.

Texto legible.

Placeholder claro.

Focus elegante.

---

# Labels

Siempre visibles.

Nunca depender únicamente del placeholder.

Utilizar:

Nombre

Correo

Contraseña

etc.

---

# Placeholders

Deben ayudar.

Ejemplo:

Ingresa el correo institucional.

Nunca repetir exactamente el Label.

---

# Estados

Normal

Hover

Focus

Success

Error

Disabled

Readonly

Todos claramente diferenciados.

---

# Focus

El focus debe ser muy visible.

Utilizar:

borde

sombra

color primario

Nunca eliminar el outline sin reemplazarlo.

---

# Validaciones

Mostrar errores inmediatamente.

No utilizar alert().

Utilizar mensajes debajo del campo.

Ejemplo:

Correo inválido.

---

# Iconos

Agregar iconos únicamente cuando aporten claridad.

Ejemplos:

Correo

Usuario

Teléfono

Calendario

Ubicación

Contraseña

---

# Select

Utilizar dropdowns modernos.

Con búsqueda cuando existan muchas opciones.

---

# Date Picker

Debe verse moderno.

Fácil de utilizar.

Responsive.

---

# Textarea

Altura mínima:

120px

Permitir redimensionar cuando tenga sentido.

---

# Checkboxes

Grandes.

Separación amplia.

Muy fáciles de pulsar.

---

# Radio Buttons

Nunca demasiado pequeños.

Excelente contraste.

---

# Switch

Preferir switches modernos.

Con animaciones suaves.

---

# Botones

Primario

Naranja.

Secundario

Azul Marino.

Cancelar

Gris.

Eliminar

Rojo.

---

# Agrupación

Los botones deben alinearse correctamente.

Desktop

Derecha.

Móvil

Ancho completo cuando mejore la experiencia.

---

# Formularios largos

Dividir mediante:

Secciones

Cards

Tabs

Stepper

Accordion

Nunca mostrar 40 campos seguidos.

---

# Ayudas

Agregar texto de ayuda únicamente cuando aporte valor.

No saturar.

---

# Errores

Nunca utilizar ventanas emergentes.

Mostrar errores debajo del campo.

Mantener excelente contraste.

---

# Éxito

Mostrar mensajes discretos.

Ejemplo:

Información guardada correctamente.

---

# Responsive

Desktop

Múltiples columnas.

Tablet

Dos columnas.

Móvil

Una columna.

Padding amplio.

Botones cómodos.

---

# Animaciones

Focus

Fade

Hover

Scale

200ms

---

# Accesibilidad

Todos los campos deben tener:

Label

Asociación correcta

ARIA cuando aplique

Contraste AA

Objetivos táctiles mínimos de 44px

---

# Rendimiento

No utilizar animaciones pesadas.

Evitar sombras excesivas.

Mantener tiempos de respuesta rápidos.

---

# Resultado Esperado

Los formularios deben sentirse como una aplicación profesional de 2026.

Deben ser:

- Elegantes
- Modernos
- Muy fáciles de completar
- Altamente responsivos
- Consistentes
- Accesibles
- Rápidos
- Claros
# 10. ANIMACIONES Y MICROINTERACCIONES

## Filosofía

Las animaciones deben mejorar la experiencia del usuario, nunca distraerlo.

Toda animación debe sentirse natural, rápida, elegante y fluida.

Inspirarse en:

- Apple
- Linear
- Notion
- Vercel
- Framer
- Stripe Dashboard

Nunca utilizar animaciones exageradas.

La prioridad siempre será el rendimiento.

---

# Principios

Las animaciones deben:

✓ Guiar al usuario.

✓ Mostrar cambios de estado.

✓ Mejorar la percepción de velocidad.

✓ Dar retroalimentación inmediata.

✓ Hacer que la interfaz se sienta viva.

Nunca deben:

✗ Molestar.

✗ Retrasar acciones.

✗ Generar mareos.

✗ Consumir demasiados recursos.

---

# Duraciones

Micro interacción

100ms – 150ms

Hover

150ms

Botones

150ms

Inputs

150ms

Cards

200ms

Dropdown

200ms

Modal

250ms

Sidebar

250ms

Drawer

250ms

Página

250ms

Dashboard

250ms

Toast

200ms

Alert

200ms

---

# Curvas de Animación

Preferir:

ease

ease-in-out

cubic-bezier(.2,.8,.2,1)

Evitar curvas bruscas.

---

# Hover

Los elementos interactivos deben responder al pasar el cursor.

Aplicar en:

Botones

Cards

Tarjetas

Items

Sidebar

Menús

Tablas

Widgets

El hover debe incluir únicamente cambios sutiles como:

• Elevación ligera.

• Cambio suave de color.

• Incremento pequeño de sombra.

• Escala máxima de 1.02.

Nunca realizar movimientos exagerados.

---

# Focus

Todos los elementos interactivos deben mostrar claramente el foco.

Utilizar:

Outline moderno.

Glow muy ligero.

Cambio de borde.

Nunca eliminar el focus.

---

# Botones

Estados:

Normal

Hover

Pressed

Focus

Disabled

Loading

Transiciones suaves.

No usar rebotes.

---

# Inputs

Animar:

Focus

Validación

Error

Success

Placeholder

Label

La animación debe durar entre 150 y 200 ms.

---

# Cards

Al aparecer:

Fade + Slide.

Al hacer hover:

Sombra ligeramente mayor.

Leve elevación.

Nunca más de 4 px de desplazamiento.

---

# Dashboard

Los widgets deben aparecer con:

Fade

Slide Up

Duración escalonada.

Cada widget puede retrasarse entre 30 y 60 ms respecto al anterior.

Esto mejora la percepción visual.

---

# Sidebar

La apertura debe ser fluida.

Nunca brusca.

Utilizar transición de 250 ms.

Los iconos deben aparecer suavemente.

---

# Menús

Dropdown

Popover

Context Menu

Fade + Scale.

Nunca aparecer instantáneamente.

---

# Modales

Animación:

Opacity

Scale

Slide ligero

Duración:

250 ms.

Cerrar utilizando la animación inversa.

---

# Toast

Fade In

Fade Out

No utilizar rebotes.

---

# Alertas

Aparecer suavemente.

No bloquear visualmente al usuario.

---

# Loading

Preferir:

Skeleton

Shimmer

Progress

Nunca utilizar spinners infinitos cuando exista otra alternativa.

---

# Skeleton Loading

El Skeleton debe parecer el contenido final.

Mantener proporciones reales.

No crear placeholders aleatorios.

---

# Cambios de Página

Utilizar:

Fade

Slide

Cross Fade

Nunca realizar transiciones largas.

Máximo:

250 ms.

---

# Scroll

Scroll completamente fluido.

No modificar el comportamiento natural del navegador.

---

# Microinteracciones

Aplicar microinteracciones en:

✓ Botones

✓ Links

✓ Cards

✓ Tabs

✓ Sidebar

✓ Inputs

✓ Checkboxes

✓ Radios

✓ Switches

✓ Dropdowns

✓ Calendarios

✓ Tablas

✓ Widgets

---

# Estados

Todos los componentes deben tener:

Hover

Focus

Pressed

Disabled

Loading

Success

Warning

Error

---

# Rendimiento

Las animaciones deben usar preferentemente:

transform

opacity

Evitar animar:

width

height

left

top

margin

Siempre que sea posible.

---

# Prefers Reduced Motion

Respetar:

prefers-reduced-motion

Si el usuario lo solicita:

Reducir animaciones.

Eliminar movimientos innecesarios.

Mantener únicamente cambios de opacidad.

---

# Objetivo

Las animaciones deben transmitir:

Profesionalismo.

Rapidez.

Modernidad.

Calidad.

Suavidad.

Nunca espectáculo.



# 11. ACCESIBILIDAD (WCAG 2.2)

## Filosofía

Todo el sistema debe cumplir las recomendaciones WCAG 2.2 nivel AA como mínimo.

La accesibilidad forma parte del diseño.

Nunca debe considerarse opcional.

---

# Objetivos

Crear una interfaz usable para:

Usuarios con baja visión.

Usuarios con daltonismo.

Usuarios con movilidad reducida.

Usuarios que utilizan teclado.

Usuarios que utilizan lectores de pantalla.

Usuarios mayores.

---

# Contraste

Cumplir como mínimo:

AA

Preferentemente:

AAA

Evitar textos con poco contraste.

---

# Tipografía

Nunca usar:

Texto menor a 14 px.

Preferir:

16 px para contenido.

18 px para subtítulos.

22 px para títulos.

28 px para encabezados.

---

# Altura de Línea

Entre:

1.4

y

1.7

Facilita la lectura.

---

# Espaciado

Mantener suficiente separación entre:

Botones

Inputs

Cards

Enlaces

No saturar interfaces.

---

# Botones

Área mínima táctil:

44 x 44 px.

Ideal:

48 x 48 px.

---

# Inputs

Todos deben tener:

Label.

Placeholder.

Descripción cuando sea necesaria.

Nunca depender únicamente del placeholder.

---

# Focus

Todos los elementos interactivos deben tener un foco claramente visible.

Nunca eliminar outline.

Si se personaliza, debe ser aún más visible.

---

# Navegación por Teclado

Todo debe funcionar usando únicamente:

Tab

Shift + Tab

Enter

Espacio

Escape

Flechas cuando corresponda.

---

# Orden del Tab

El recorrido debe ser lógico.

No saltar elementos.

---

# Formularios

Mostrar errores claros.

Indicar cómo corregirlos.

No utilizar únicamente color rojo.

Agregar:

Icono

Texto

Color

---

# Colores

Nunca comunicar información únicamente mediante color.

Siempre acompañar con:

Iconos.

Texto.

Etiquetas.

---

# Iconografía

Los iconos importantes deben tener texto o tooltip cuando sea necesario.

No depender únicamente del icono.

---

# Enlaces

Los enlaces deben ser claramente identificables.

No depender solo del color.

---

# Tablas

Permitir lectura sencilla.

Encabezados claros.

Espaciado adecuado.

Scroll horizontal solo cuando sea indispensable.

---

# Imágenes

Toda imagen informativa debe tener:

Texto alternativo.

Las imágenes decorativas deben marcarse correctamente.

---

# Lectores de Pantalla

Utilizar atributos ARIA cuando aporten valor.

Ejemplos:

aria-label

aria-describedby

aria-expanded

aria-hidden

role

No abusar de ARIA cuando HTML semántico sea suficiente.

---

# HTML Semántico

Preferir:

header

main

section

article

aside

nav

footer

button

label

form

Evitar abusar de div.

---

# Errores

Los mensajes deben ser:

Clarísimos.

Educados.

Útiles.

Explicar cómo resolver el problema.

---

# Loading

Informar al usuario cuando una acción esté en proceso.

No dejar interfaces congeladas.

---

# Responsive

La accesibilidad debe mantenerse en:

HD

Full HD

2K

4K

Ultrawide

Laptop

Tablet

Móvil

---

# Zoom

La interfaz debe seguir funcionando correctamente con:

125%

150%

175%

200%

de zoom.

---

# Objetivo Final

La interfaz debe ser:

✓ Fácil de leer.

✓ Fácil de entender.

✓ Fácil de navegar.

✓ Fácil de utilizar.

✓ Accesible para la mayor cantidad posible de usuarios.

El diseño debe sentirse moderno, limpio, profesional y completamente inclusivo.
# 12. DARK MODE

## Objetivo

La interfaz debe estar preparada para soportar un tema oscuro sin necesidad de reescribir los componentes.

Todo el sistema debe construirse utilizando variables de color y nunca colores fijos cuando sea posible.

---

## Filosofía

El modo oscuro no consiste únicamente en invertir colores.

Debe:

- Reducir la fatiga visual.
- Mantener una excelente legibilidad.
- Conservar la identidad visual del sistema.
- Mantener la jerarquía visual.
- Evitar negros absolutos (#000000) salvo casos muy específicos.

---

## Colores recomendados

### Fondo principal

```css
#111827
```

---

### Fondo secundario

```css
#1F2937
```

---

### Tarjetas

```css
#1E293B
```

---

### Surface Elevation

```css
#273449
```

---

### Texto principal

```css
#F9FAFB
```

---

### Texto secundario

```css
#CBD5E1
```

---

### Bordes

```css
rgba(255,255,255,.08)
```

---

## Colores de marca

Mantener los mismos colores del modo claro.

Naranja

```css
#F57C00
```

Azul Marino

```css
#0D47A1
```

Rojo

```css
#D32F2F
```

Solo ajustar brillo cuando sea necesario.

---

## Sombras

En Dark Mode las sombras deben ser mucho más suaves.

Preferir:

```css
box-shadow:
0 8px 20px rgba(0,0,0,.35);
```

Evitar sombras negras muy fuertes.

---

## Contraste

Todos los textos deben cumplir como mínimo WCAG AA.

Nunca utilizar:

Texto gris sobre fondo gris.

---

## Tarjetas

Las tarjetas deben destacar mediante:

- Elevación
- Bordes suaves
- Sombras
- Contraste

No mediante colores exagerados.

---

## Inputs

Los inputs deben mantener:

Focus visible.

Placeholder legible.

Errores claros.

Success visibles.

---

## Botones

El botón primario siempre debe conservar el color naranja.

No convertirlo a gris.

---

## Sidebar

Debe utilizar un tono ligeramente más oscuro que el contenido principal.

Debe diferenciar claramente:

Elemento activo

Elemento hover

Elemento seleccionado

---

## Navbar

Debe mantener:

Elevación

Separación

Excelente contraste

---

## Modales

Los modales deben destacar mediante:

Oscurecimiento del fondo.

Elevación.

Bordes.

No únicamente por el color.

---

## Tablas

Las tablas deben mantener:

Cabeceras claras.

Filas diferenciadas.

Hover visible.

Líneas discretas.

---

## Gráficas

Los colores deben seguir siendo distinguibles.

No utilizar tonos demasiado oscuros.

---

## Iconos

Los iconos deben mantener suficiente contraste.

No utilizar gris oscuro sobre fondo oscuro.

---

## Estados

Success

Warning

Danger

Info

Deben seguir siendo reconocibles tanto en Light como Dark Mode.

---

## Cambio de tema

Todo el sistema debe poder cambiar entre Light y Dark utilizando únicamente variables CSS.

Nunca modificar manualmente cientos de clases.

---

## Variables

Ejemplo

```css
:root{

--bg:#F8F9FB;

--surface:#FFFFFF;

--text:#1F2937;

}

[data-theme="dark"]{

--bg:#111827;

--surface:#1F2937;

--text:#F9FAFB;

}
```

---

## Rendimiento

No duplicar estilos.

Utilizar variables.

Evitar CSS repetido.

---

## Resultado esperado

El usuario debe sentir que el Dark Mode fue diseñado desde el inicio y no agregado posteriormente.



# 13. CHECKLIST FINAL DE CALIDAD

## Antes de finalizar cualquier vista

Debe verificarse absolutamente todo.

---

## Diseño

✓ La vista mantiene una jerarquía visual clara.

✓ Existe suficiente espacio entre componentes.

✓ No hay elementos desalineados.

✓ Los colores respetan la identidad visual.

✓ La interfaz luce moderna.

✓ El diseño transmite profesionalismo.

---

## Layout

✓ No existen espacios vacíos innecesarios.

✓ Los contenedores están correctamente alineados.

✓ El contenido aprovecha bien el espacio disponible.

✓ El dashboard mantiene una buena distribución.

✓ Las tarjetas tienen tamaños consistentes.

---

## Responsive

Verificar en:

✓ HD

✓ Full HD

✓ 2K

✓ 4K

✓ Ultrawide

✓ Laptop

✓ Tablet

✓ iPad

✓ Móvil Android

✓ iPhone

No debe existir:

Scroll horizontal.

Contenido cortado.

Componentes desalineados.

Botones fuera de pantalla.

Texto truncado.

---

## Componentes

Verificar:

Navbar.

Sidebar.

Cards.

Botones.

Inputs.

Tablas.

Gráficas.

Calendarios.

Dropdowns.

Modales.

Alertas.

Paginación.

Widgets.

Estados vacíos.

Loading.

---

## Formularios

✓ Todos los campos son visibles.

✓ Los labels son claros.

✓ Los mensajes de error funcionan.

✓ Los botones siguen funcionando.

✓ No cambió ninguna validación.

---

## Tablas

✓ Responsive.

✓ Hover correcto.

✓ Paginación funcional.

✓ Filtros visibles.

✓ Excelente legibilidad.

---

## Animaciones

✓ Suaves.

✓ Cortas.

✓ Consistentes.

✓ Sin afectar el rendimiento.

---

## Accesibilidad

✓ Navegación por teclado.

✓ Focus visible.

✓ Contraste WCAG AA.

✓ Tamaños táctiles adecuados.

✓ Labels correctos.

---

## Rendimiento

✓ CSS limpio.

✓ Sin duplicación.

✓ Sin estilos innecesarios.

✓ Buen rendimiento.

✓ Sin animaciones pesadas.

---

## Django

Verificar:

✓ No cambió la lógica.

✓ No cambiaron Models.

✓ No cambiaron Views.

✓ No cambiaron URLs.

✓ No cambiaron APIs.

✓ No cambiaron consultas.

✓ No cambiaron permisos.

✓ No cambiaron autenticación.

✓ No cambiaron migraciones.

✓ No cambió ninguna funcionalidad.

---

## JavaScript

✓ Eventos funcionando.

✓ IDs intactos.

✓ data-* intactos.

✓ AJAX funcionando.

✓ HTMX funcionando.

✓ Alpine funcionando.

✓ Scripts funcionando.

---

## Calidad Visual

La aplicación debe sentirse como un producto SaaS premium de 2026.

Inspiración:

• Apple

• Stripe

• Linear

• Notion

• GitHub

• Vercel

• Figma

Debe transmitir:

Profesionalismo.

Elegancia.

Rapidez.

Minimalismo.

Claridad.

Consistencia.

---

## Regla Final

No considerar una vista terminada hasta cumplir todos los puntos anteriores.

Si existe un conflicto entre mejorar el diseño o conservar la funcionalidad, la funcionalidad siempre tiene prioridad.

La misión es mejorar la experiencia visual al máximo sin alterar el comportamiento del sistema.
# DESIGN_SYSTEM.md

Version: 1.0

Autor: Equipo de Diseño

Propósito:

Este documento define el Sistema de Diseño oficial del proyecto.

Todas las vistas, componentes, páginas y funcionalidades deberán seguir estas reglas para mantener una experiencia consistente.

Este documento tiene prioridad sobre cualquier decisión visual automática del modelo.

Nunca sacrificar consistencia por creatividad.

---

# FILOSOFÍA DEL DISEÑO

El sistema debe transmitir una sensación de software profesional, moderno y confiable.

No debe parecer una plantilla.

No debe parecer Bootstrap.

No debe parecer un dashboard genérico.

Debe sentirse como una plataforma desarrollada específicamente para este proyecto.

Inspiración:

• Apple

• Notion

• Linear

• Stripe

• Framer

• GitHub

• Craft

• Arc Browser

• Raycast

• Vercel

No copiar ninguno.

Solo inspirarse en:

• jerarquía

• organización

• claridad

• simplicidad

• elegancia

---

# PRINCIPIOS

Cada pantalla debe responder a estos principios.

## Claridad

El usuario debe entender la interfaz inmediatamente.

No agregar elementos innecesarios.

Eliminar ruido visual.

Mantener espacios amplios.

---

## Simplicidad

Menos elementos.

Más espacio.

Más claridad.

No sobrecargar la interfaz.

---

## Consistencia

Todos los botones iguales.

Todos los formularios iguales.

Todas las tarjetas iguales.

Todos los iconos siguen el mismo estilo.

Todos los colores mantienen la misma función.

---

## Escalabilidad

El diseño debe crecer sin romperse.

Nuevos módulos deben verse iguales.

Nuevas páginas deben integrarse naturalmente.

---

## Accesibilidad

Todos los componentes deben ser legibles.

No utilizar contrastes bajos.

No utilizar textos pequeños.

No depender únicamente del color.

---

## Productividad

El sistema debe permitir trabajar muchas horas.

No cansar la vista.

No utilizar colores agresivos.

No utilizar sombras exageradas.

---

# PERSONALIDAD DEL PRODUCTO

La interfaz debe sentirse:

Profesional

Minimalista

Elegante

Confiable

Moderna

Tecnológica

Ordenada

Rápida

Limpia

Inteligente

Nunca debe sentirse:

Infantil

Colorida en exceso

Sobrecargada

Antigua

Desordenada

Pesada

Confusa

---

# ESTILO GENERAL

Base:

Soft UI

Complemento:

Cupertino

Detalle:

Neumorphism ligero

Nunca utilizar neumorphism extremo.

Nunca utilizar glassmorphism excesivo.

Nunca utilizar skeuomorphism.

---

# JERARQUÍA VISUAL

Todo elemento debe comunicar importancia.

Orden:

Título principal

↓

Título

↓

Subtítulo

↓

Contenido

↓

Texto secundario

↓

Texto auxiliar

↓

Ayuda

El usuario debe identificar inmediatamente qué es importante.

---

# ESPACIOS EN BLANCO

El espacio es parte del diseño.

Nunca intentar llenar todos los huecos.

Más espacio = mejor experiencia.

Regla:

Cuando exista duda entre agregar contenido o dejar espacio vacío, dejar espacio vacío.

---

# ALINEACIÓN

Todo debe alinearse.

Nunca colocar elementos visualmente desordenados.

Mantener líneas imaginarias.

Todos los botones deben compartir alineación.

Todas las tarjetas deben compartir alineación.

Todos los formularios deben compartir alineación.

---

# RITMO VISUAL

El usuario debe recorrer la pantalla naturalmente.

Utilizar bloques.

Separar secciones.

No crear muros de información.

Agrupar elementos relacionados.

---

# DENSIDAD

Utilizar densidad media.

No utilizar interfaces extremadamente compactas.

No utilizar interfaces excesivamente separadas.

Buscar equilibrio.

---

# SISTEMA DE MEDIDAS

Base:

8px

Todo debe derivarse del sistema de 8 puntos.

Ejemplos:

4

8

16

24

32

40

48

56

64

80

96

Nunca utilizar valores aleatorios.

---

# RADIOS

Inputs

16px

Botones

18px

Cards

22px

Modales

24px

Widgets

24px

Dashboard

24px

---

# SOMBRAS

Siempre suaves.

Nunca oscuras.

Nunca exageradas.

Preferir varias sombras pequeñas antes que una muy fuerte.

Ejemplo:

0 8px 30px rgba(15,23,42,.08)

---

# BORDES

Muy discretos.

Utilizar:

#E5E7EB

Nunca utilizar bordes negros.

Nunca utilizar bordes gruesos.

---

# PROFUNDIDAD

Utilizar máximo tres niveles.

Nivel 1

Contenido

Nivel 2

Cards

Nivel 3

Modales

Nunca generar demasiada profundidad.

---

# ESQUINAS

Todo debe sentirse suave.

No utilizar esquinas completamente cuadradas.

Mantener coherencia en toda la aplicación.

---

# ICONOGRAFÍA

Usar un solo estilo.

Preferentemente:

Lucide

Heroicons

Ionicons

Nunca mezclar estilos.

Todos los iconos deben compartir grosor.

Todos los iconos deben compartir tamaño proporcional.

---

# TAMAÑOS DE ICONOS

Pequeño

16px

Normal

20px

Grande

24px

Dashboard

28px

Nunca utilizar tamaños aleatorios.

---

# ILUSTRACIONES

Cuando existan estados vacíos.

Utilizar ilustraciones minimalistas.

No utilizar imágenes infantiles.

No utilizar cliparts.

---

# FOTOGRAFÍAS

Cuando sean necesarias.

Utilizar fotografías limpias.

Buena iluminación.

Alta resolución.

Nunca fotografías pixeladas.

Nunca fotografías con marcas de agua.

---

# AVATARES

Redondos.

Con iniciales cuando no exista fotografía.

Mantener consistencia.

---

# DIVISORES

Utilizar únicamente cuando realmente ayuden.

Evitar líneas innecesarias.

Preferir separación mediante espacio.

---

# TARJETAS

Las tarjetas son el componente principal del sistema.

Características:

Mucho padding.

Sombras suaves.

Bordes redondeados.

Jerarquía clara.

Contenido bien organizado.

Nunca saturarlas.

---

# BOTONES

Siempre destacar una acción principal.

Nunca mostrar cinco botones primarios juntos.

Jerarquía:

Primario

Secundario

Terciario

Texto

Peligro

Cada pantalla debe tener una acción principal evidente.
# 3. VARIABLES CSS (DESIGN TOKENS)

## Objetivo

Todo el sistema visual debe construirse utilizando Design Tokens.

Nunca utilizar colores, tamaños o espaciados directamente dentro de los componentes cuando puedan representarse mediante variables.

Todas las vistas deben reutilizar los mismos tokens para mantener consistencia visual.

---

# Colores Principales

```css
:root{

--color-primary:#F57C00;
--color-primary-hover:#E56E00;
--color-primary-light:#FFF2E8;

--color-secondary:#0D47A1;
--color-secondary-hover:#0B3D91;
--color-secondary-light:#EAF2FD;

--color-danger:#D32F2F;
--color-danger-hover:#B71C1C;
--color-danger-light:#FDECEC;

--color-success:#22C55E;
--color-success-light:#ECFDF3;

--color-warning:#F59E0B;
--color-warning-light:#FFF7E6;

--color-info:#3B82F6;
--color-info-light:#EFF6FF;

}
```

---

# Colores de Fondo

```css
:root{

--bg-page:#F8F9FB;

--bg-surface:#FFFFFF;

--bg-surface-secondary:#F3F5F8;

--bg-card:#FFFFFF;

--bg-hover:#F7F8FA;

--bg-disabled:#ECECEC;

}
```

---

# Colores de Texto

```css
:root{

--text-primary:#1F2937;

--text-secondary:#6B7280;

--text-muted:#9CA3AF;

--text-disabled:#C4C4C4;

--text-white:#FFFFFF;

}
```

---

# Bordes

```css
:root{

--border-light:#E5E7EB;

--border-medium:#D1D5DB;

--border-dark:#9CA3AF;

}
```

---

# Sombras

Nunca utilizar sombras exageradas.

```css
:root{

--shadow-xs:0 1px 2px rgba(0,0,0,.05);

--shadow-sm:0 4px 10px rgba(15,23,42,.05);

--shadow-md:0 8px 30px rgba(15,23,42,.08);

--shadow-lg:0 20px 45px rgba(15,23,42,.12);

--shadow-xl:0 30px 60px rgba(15,23,42,.15);

}
```

---

# Bordes Redondeados

```css
:root{

--radius-xs:6px;

--radius-sm:10px;

--radius-md:16px;

--radius-lg:20px;

--radius-xl:28px;

--radius-pill:999px;

}
```

---

# Espaciado

Todo el proyecto debe utilizar un sistema de 8 puntos.

```css
:root{

--space-1:4px;

--space-2:8px;

--space-3:12px;

--space-4:16px;

--space-5:20px;

--space-6:24px;

--space-7:32px;

--space-8:40px;

--space-9:48px;

--space-10:64px;

}
```

---

# Duración de Animaciones

```css
:root{

--transition-fast:150ms;

--transition-normal:220ms;

--transition-slow:320ms;

}
```

---

# Tipografía

```css
:root{

--font-family:"Inter","SF Pro Display",sans-serif;

--font-size-xs:12px;

--font-size-sm:14px;

--font-size-md:16px;

--font-size-lg:18px;

--font-size-xl:22px;

--font-size-2xl:28px;

--font-size-3xl:36px;

}
```

---

# Peso de Fuente

```css
:root{

--font-light:300;

--font-regular:400;

--font-medium:500;

--font-semibold:600;

--font-bold:700;

}
```

---

# Reglas

Nunca repetir valores.

Siempre utilizar variables.

Mantener consistencia visual en todo el sistema.

No utilizar colores hardcodeados.

No utilizar tamaños fijos cuando exista una variable equivalente.

Todos los componentes deben depender de este sistema.

=======================================================================

# 4. SISTEMA DE LAYOUT Y GRID

## Objetivo

El diseño debe adaptarse automáticamente a cualquier resolución.

No diseñar pensando únicamente en Full HD.

Debe aprovechar correctamente el espacio disponible.

---

# Breakpoints

Utilizar los siguientes puntos de ruptura.

```scss
$mobile:576px;

$tablet:768px;

$laptop:1024px;

$desktop:1280px;

$desktop-xl:1536px;

$desktop-2k:1920px;

$desktop-4k:2560px;
```

---

# Layout General

Desktop

Sidebar fija.

Header superior.

Contenido principal.

Paneles.

Widgets.

Dashboard.

---

Tablet

Sidebar colapsable.

Contenido reorganizado.

Dashboard de 2 o 3 columnas.

---

Móvil

Drawer.

Contenido vertical.

Una sola columna.

---

# Grid

Utilizar únicamente:

CSS Grid

Flexbox

Nunca tablas para construir layouts.

---

Ejemplo

```css
grid-template-columns:

repeat(auto-fit,minmax(320px,1fr));
```

---

# Columnas

Desktop

4-6 columnas.

Tablet

2-3 columnas.

Móvil

1 columna.

---

# Contenedores

Todo el contenido debe utilizar un ancho máximo.

Ejemplo:

```css
max-width:1600px;

margin:auto;
```

No dejar contenido pegado a los bordes.

---

# Espaciado

Todo debe seguir el sistema de 8 puntos.

Nunca utilizar márgenes aleatorios.

---

# Tarjetas

Todas las tarjetas deben mantener:

Padding amplio.

Bordes redondeados.

Sombras suaves.

Alturas consistentes.

---

# Dashboards

Utilizar Grid.

Nunca utilizar posiciones absolutas.

Los widgets deben reorganizarse automáticamente.

---

# Tablas

Desktop

Tabla completa.

Tablet

Scroll horizontal únicamente cuando sea necesario.

Móvil

Transformar la tabla en tarjetas cuando sea posible.

---

# Sidebar

Desktop

Siempre visible.

Tablet

Colapsable.

Móvil

Drawer.

---

# Header

Siempre fijo.

Altura consistente.

Acciones alineadas.

Buscador.

Perfil.

Notificaciones.

---

# Formularios

Desktop

2-4 columnas.

Tablet

2 columnas.

Móvil

1 columna.

---

# Responsive

Obligatorio soportar:

HD

Full HD

2K

4K

Ultrawide

Laptop

Tablet

Móvil

---

# Escalabilidad

Utilizar:

clamp()

min()

max()

minmax()

auto-fit

auto-fill

Flexbox

Grid

Container Queries cuando sea posible.

---

# Evitar

Width fijos.

Height fijos.

Posiciones absolutas innecesarias.

Scroll horizontal.

Elementos demasiado pequeños.

Grandes espacios vacíos.

---

# Resultado esperado

Cada página debe aprovechar inteligentemente el espacio disponible.

No debe verse igual en un móvil que en un monitor 4K.

La interfaz debe reorganizarse automáticamente ofreciendo siempre la mejor experiencia de usuario posible.

Todo el sistema debe sentirse como un software SaaS premium desarrollado en 2026.
# 5. Sistema de Iconografía

## Objetivo

La iconografía debe mejorar la comprensión de la interfaz y facilitar la navegación.

Los iconos nunca deben utilizarse únicamente como decoración.

Cada icono debe tener un propósito claro.

---

# Biblioteca de iconos

Utilizar únicamente una biblioteca consistente durante todo el proyecto.

Orden de preferencia:

1. Bootstrap Icons
2. Heroicons
3. Font Awesome
4. Material Symbols

Nunca mezclar varias bibliotecas de iconos dentro de la misma interfaz.

---

# Tamaños

Extra pequeño

14px

Pequeño

16px

Normal

20px

Mediano

24px

Grande

32px

Extra grande

48px

---

# Espaciado

Todo icono debe tener separación respecto al texto.

Espaciado recomendado

8px

Nunca pegar iconos al texto.

---

# Colores

Los iconos deben heredar el color del componente.

Ejemplos

Botón primario

icono blanco

Botón secundario

icono azul

Error

icono rojo

Advertencia

icono naranja

Éxito

icono verde

Información

icono azul

Nunca utilizar colores diferentes sin una razón funcional.

---

# Peso visual

Los iconos deben mantener un mismo grosor.

No mezclar:

Outlined

Filled

Rounded

Sharp

en una misma pantalla.

Elegir un estilo y mantenerlo en todo el sistema.

---

# Iconos por acción

Guardar

save

Editar

edit

Eliminar

delete

Buscar

search

Agregar

add

Cerrar

close

Cancelar

close

Aceptar

check

Volver

arrow_back

Siguiente

arrow_forward

Descargar

download

Subir archivo

upload

Configuración

settings

Usuario

person

Grupo

groups

Calendario

calendar_today

Notificaciones

notifications

Inicio

home

Estadísticas

analytics

Dashboard

dashboard

Reportes

description

Perfil

account_circle

Seguridad

shield

Ayuda

help

Información

info

Advertencia

warning

Error

error

Éxito

check_circle

---

# Botones con iconos

El icono siempre debe alinearse verticalmente.

Utilizar flexbox.

No utilizar márgenes negativos.

Ejemplo

[ Icono ] Texto

Nunca

Texto Icono Pegado

---

# Inputs

Cuando el icono aporte contexto puede colocarse:

Dentro del input

o

Como prefijo.

Ejemplo

Usuario

[👤 Usuario]

Correo

[@ Correo]

Buscar

[🔍 Buscar...]

---

# Dashboard

Los widgets pueden utilizar iconos grandes.

Entre 32 y 48 px.

Nunca competir visualmente con el dato principal.

---

# Sidebar

Todos los elementos deben tener icono.

Texto + Icono.

Mantener la misma alineación.

---

# Navbar

Utilizar únicamente iconos importantes.

Evitar sobrecargar la navegación.

---

# Accesibilidad

Todo icono interactivo debe tener:

aria-label

title

tooltip cuando sea necesario

Los iconos nunca deben ser el único medio para comunicar información importante.

Siempre acompañarlos de texto cuando la acción no sea completamente evidente.

---

# Buenas prácticas

✔ Iconos consistentes.

✔ Mismo tamaño dentro de un mismo contexto.

✔ Mismo grosor.

✔ Mismo color por estado.

✔ Mucho espacio entre icono y texto.

✔ Alineación perfecta.

✔ Excelente legibilidad.

---
# 7. PATRONES UX

## Objetivo

Cada interacción debe ser intuitiva, rápida y consistente.

El usuario nunca debe preguntarse:

- ¿Dónde está esta opción?
- ¿Qué hace este botón?
- ¿Qué acaba de pasar?
- ¿Dónde debo hacer clic?

Todo debe ser evidente desde el primer momento.

---

# Principios UX

La interfaz debe seguir estos principios:

- Simplicidad
- Consistencia
- Claridad
- Rapidez
- Accesibilidad
- Retroalimentación inmediata
- Prevención de errores
- Recuperación sencilla

---

# Jerarquía Visual

Toda pantalla debe responder inmediatamente:

1. ¿Dónde estoy?
2. ¿Qué puedo hacer?
3. ¿Qué información es importante?
4. ¿Cuál es la siguiente acción?

La jerarquía debe construirse mediante:

- Tamaño
- Peso tipográfico
- Color
- Espaciado
- Contraste
- Agrupación

Nunca únicamente mediante colores.

---

# Distribución

Toda pantalla debe dividirse en:

Header

↓

Contenido principal

↓

Acciones principales

↓

Información secundaria

↓

Footer (cuando exista)

Nunca mezclar acciones importantes con información secundaria.

---

# Ley de Proximidad

Los elementos relacionados deben permanecer juntos.

Ejemplo:

Nombre

Correo

Teléfono

Dirección

deben pertenecer al mismo grupo visual.

No dejar espacios grandes entre elementos relacionados.

---

# Ley de Similaridad

Los componentes con la misma función deben verse iguales.

Todos los botones principales:

- mismo color
- mismo tamaño
- mismo radio
- misma sombra

Todos los botones secundarios:

- mismo estilo

Todos los inputs:

- mismo diseño

Toda la aplicación debe sentirse consistente.

---

# Acciones Primarias

Cada pantalla debe tener solamente UNA acción principal.

Ejemplos:

Guardar

Enviar

Crear

Actualizar

Finalizar

Debe destacar visualmente.

---

# Acciones Secundarias

Cancelar

Volver

Cerrar

Editar

Duplicar

No deben competir visualmente con la acción principal.

---

# Acciones Destructivas

Eliminar

Cancelar definitivamente

Vaciar

Cerrar sesión

Siempre utilizar rojo.

Solicitar confirmación.

Nunca ejecutar inmediatamente.

---

# Navegación

La navegación debe ser evidente.

El usuario nunca debe perderse.

Utilizar:

Sidebar

Breadcrumbs

Tabs

Menus

Back Button

cuando sea apropiado.

---

# Dashboard

Todo dashboard debe responder rápidamente:

¿Qué pasó?

¿Qué está pasando?

¿Qué requiere atención?

Debe mostrar primero:

KPIs

↓

Actividad reciente

↓

Gráficas

↓

Información secundaria

---

# Formularios

Reducir el esfuerzo del usuario.

Agrupar campos.

Evitar formularios extremadamente largos.

Cuando sea posible:

utilizar múltiples columnas.

---

# Confirmaciones

Siempre mostrar retroalimentación.

Ejemplos:

Guardado correctamente.

Actualizado.

Eliminado.

Error.

Nunca dejar al usuario sin respuesta.

---

# Estados Vacíos

Nunca mostrar pantallas vacías.

Mostrar:

Ilustración

Mensaje

Descripción

Botón principal

Ejemplo:

"No existen alumnos registrados"

[Agregar alumno]

---

# Estados de Carga

Mostrar Skeletons.

Nunca dejar pantallas completamente blancas.

Evitar loaders infinitos.

---

# Errores

Los errores deben indicar:

Qué ocurrió.

Por qué ocurrió.

Cómo solucionarlo.

Nunca mostrar errores técnicos al usuario.

Incorrecto:

Exception...

Correcto:

"No fue posible guardar la información.
Inténtalo nuevamente."

---

# Microinteracciones

Agregar pequeñas animaciones para:

Hover

Focus

Click

Cambio de pestaña

Carga

Éxito

Error

Seleccionar

Estas animaciones deben durar entre:

180 ms

250 ms

---

# Consistencia

Un componente siempre debe comportarse igual.

Nunca cambiar el comportamiento entre páginas.

---

# Espacio en Blanco

Utilizar suficiente espacio.

Evitar pantallas saturadas.

El espacio también comunica información.

---

# Legibilidad

Nunca utilizar:

Texto pequeño

Contraste bajo

Elementos demasiado juntos

---

# Flujo Visual

El ojo debe recorrer la pantalla naturalmente.

Izquierda

↓

Arriba

↓

Centro

↓

Acción principal

---

# Diseño Escalable

Toda pantalla debe poder crecer sin romper el diseño.

Nuevos widgets.

Nuevas tarjetas.

Nuevos filtros.

Nuevas tablas.

Todo debe integrarse fácilmente.

---

# Objetivo Final

Cada pantalla debe parecer diseñada por un equipo profesional de UX y ofrecer una experiencia clara, moderna y eficiente.

--------------------------------------------------------------------------------

# 8. ACCESIBILIDAD (WCAG 2.2 AA)

## Objetivo

Toda la aplicación debe ser accesible para cualquier usuario.

La accesibilidad no es opcional.

Debe cumplir como mínimo WCAG 2.2 nivel AA.

---

# Contraste

Todo texto debe tener suficiente contraste.

Evitar:

Gris claro sobre blanco.

Azul sobre negro.

Rojo sobre naranja.

Utilizar relaciones de contraste recomendadas.

---

# Tamaño de Texto

Nunca utilizar menos de:

14px

Texto principal:

16px

Títulos:

20px o superior.

---

# Tamaño de Botones

Todo botón debe medir como mínimo:

44 x 44 px

Ideal:

48 x 48 px

---

# Áreas Táctiles

Los iconos pequeños deben tener un área táctil amplia.

Aunque el icono mida 20px.

El área clicable debe mantenerse grande.

---

# Navegación por Teclado

Toda la aplicación debe funcionar sin mouse.

Tab

Shift + Tab

Enter

Espacio

Escape

Flechas

deben funcionar correctamente.

---

# Focus Visible

Nunca eliminar:

outline

sin proporcionar un reemplazo.

Todo elemento enfocado debe ser claramente visible.

---

# Labels

Todo input debe tener:

Label

Placeholder (opcional)

Mensaje de ayuda (cuando sea necesario)

Nunca depender únicamente del placeholder.

---

# Errores de Formularios

Los errores deben mostrarse:

Cerca del campo.

Con color.

Con icono.

Con texto.

No únicamente mediante color.

---

# Iconos

Todo icono interactivo debe tener:

aria-label

o

texto alternativo.

---

# Imágenes

Toda imagen debe incluir:

alt

descriptivo.

Las imágenes decorativas deben marcarse correctamente para lectores de pantalla.

---

# Tablas

Las tablas deben utilizar:

thead

tbody

th

scope

caption cuando sea necesario.

---

# Formularios

Relacionar correctamente:

label

for

id

---

# Modales

Al abrir un modal:

Mover automáticamente el foco al contenido.

Al cerrar:

Regresar el foco al elemento que lo abrió.

---

# Toasts

No desaparecer demasiado rápido.

Permitir suficiente tiempo para leerlos.

---

# Animaciones

Respetar:

prefers-reduced-motion

Reducir animaciones cuando el usuario lo solicite.

---

# Color

Nunca utilizar únicamente el color para transmitir información.

Ejemplo incorrecto:

Campo rojo.

Ejemplo correcto:

Campo rojo

+

Icono

+

Mensaje

---

# Lectores de Pantalla

Todo componente importante debe ser entendible por lectores de pantalla.

---

# Responsive

La accesibilidad debe mantenerse en:

Desktop

Laptop

Tablet

iPad

Móvil

HD

Full HD

2K

4K

Ultrawide

---

# Zoom

La aplicación debe funcionar correctamente con zoom del navegador hasta 200%.

Sin perder funcionalidad.

---

# Objetivo Final

Cualquier usuario, independientemente de sus capacidades o dispositivo, debe poder utilizar la aplicación de forma cómoda, eficiente y segura.