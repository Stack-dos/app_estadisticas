# Changelog

Todos los cambios importantes de StatsPro, por versión.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y las versiones siguen
[Versionado Semántico](https://semver.org/lang/es/). Este archivo se genera con
[git-cliff](https://git-cliff.org/) a partir de los mensajes de commit: no se edita a mano.

## [Sin publicar]

### Agregado

- **US-103:** Casos de uso, CLI completa, tests, dependencias con uv y CI/CD ([#44](https://github.com/nicopinera/app_estadisticas/pull/44))
- Agregar carpeta de datos para archivos sensibles de Gesdeportiva
- Agregar documentación sobre el retiro de la CLI y la transición a la GUI en el Hito 1
- Agregar dependencia flet en pyproject.toml
- Implementar clase SessionManager para gestionar sesiones de usuario
- Agregar pruebas unitarias para la clase SessionManager
- Actualizar versión de Python a 3.12 en archivos de configuración y Dockerfile
- Eliminar dependencia de tabulate y ajustar requisitos de Python en archivos de configuración
- Actualizar README para reflejar la eliminación de la CLI y la transición a la aplicación de escritorio
- Actualizar RUNBOOK para reflejar la transición de la CLI a la aplicación de escritorio
- Actualizar pruebas de smoke para verificar la importación de la aplicación en lugar de la CLI
- Actualizar documentación para reflejar la transición de la CLI a la aplicación de escritorio y agregar informe de sesión sobre la GUI base
- Eliminar la CLI y actualizar el punto de entrada para abrir la aplicación de escritorio
- Eliminar funciones de la CLI y ajustar documentación en utils.py
- Eliminar función de apertura de conexión de la CLI en database_manager.py
- Agregar pruebas de integración y unitarias para la nueva GUI sin CLI, incluyendo manejo de errores y navegación
- Agregar manejador de errores para la GUI, incluyendo logging y visualización de errores
- Agregar pantalla de inicio de sesión con manejo de errores y navegación
- Agregar pantalla principal de inicio de sesión con funcionalidad de cierre de sesión
- Agregar pantalla de registro de entrenador con manejo de errores y navegación
- Agregar punto de entrada para la GUI de escritorio con manejo de rutas y dependencias
- Agregar método abstracto para guardar un club con entrenador
- Agregar método para guardar un club y vincular un usuario como entrenador en una transacción atómica
- Vincular usuario como entrenador al crear un club y mejorar la funcionalidad de guardado
- Vincular usuario como entrenador al crear un club y mejorar la persistencia en la lista de clubes
- Agregar pruebas para el manejo de sesiones y clubes activos en el SessionManager
- Agregar clase SessionDTO para manejar datos de sesión de usuario
- Agregar clase abstracta SesionAlmacen para manejar la persistencia de sesiones
- Implementar clase JsonSesionAlmacen para gestionar la persistencia de sesiones en formato JSON
- Mejorar gestión de sesiones en SessionManager, incluyendo persistencia y manejo de club activo
- Agregar ruta para el archivo de sesión recordada en la carpeta del usuario
- Agregar soporte para almacenamiento de sesión en construir_dependencias
- Agregar pruebas unitarias y de integración para la gestión de clubes y sesiones, incluyendo casos de uso de creación y restauración de sesiones
- Implementar caso de uso para restaurar sesión recordada, validando usuario y club activo
- Agregar soporte para la gestión de clubes en la interfaz, incluyendo restauración de sesión y nuevas rutas
- Agregar funcionalidad "Recordarme" en la pantalla de inicio de sesión, permitiendo que la sesión persista tras el cierre de la app
- Actualizar documentación y lógica de la pantalla de inicio, incluyendo invitación a elegir club
- Implementar pantalla "Mis clubes" para crear y gestionar clubes del usuario
- Agregar validación para evitar la creación de clubes duplicados en el caso de uso de crear club
- Agregar excepción para manejar la creación de clubes con nombres duplicados
- Agregar barra superior compartida para navegación en pantallas internas
- Actualizar documentación sobre sesión recordada y navegación en pantallas internas
- Agregar pruebas de integración para la sesión recordada y club activo
- Actualizar instrucciones sobre creación de cuenta y manejo de sesión en RUNBOOK
- Agregar informe de sesión para la funcionalidad de "Recordarme" y club activo
- Actualizar documentación sobre casos de uso y arquitectura del sistema, incluyendo la gestión de sesión y el flujo de club activo
- Agregar persistencia de sesión y club activo en la GUI, incluyendo adaptador JSON y lógica de restauración
- Actualizar plan de desarrollo detallado con cambios en la gestión de ramas y pipeline de release
- Actualizar plan de desarrollo detallado con la inclusión de la US-111 para la base visual de la GUI y ajustes en las historias de usuario
- Actualizar la US-111 con la implementación de la base visual de la GUI, incluyendo decisiones de diseño y componentes compartidos
- Agregar informe de sesión para la US-111, detallando cambios en la base visual de la GUI y decisiones de diseño
- Actualizar casos de uso y pantallas asociadas para la US-112, incluyendo cambios en la gestión de jugadores y clubes
- Actualizar la documentación de la GUI con cambios en la base visual y el menú lateral para la US-111
- Agregar nuevos íconos y fuentes a la aplicación, incluyendo el logo y el isotipo en diferentes formatos
- Mejorar ayudantes de pruebas para controles de Flet y agregar tests de la base visual y navegación
- Agregar ruta para el directorio de assets en la configuración de rutas
- Aplicar tema a la ventana y definir directorio de assets en la ejecución de la app
- Actualizar la barra superior para reflejar cambios en la navegación y el logo
- Agregar tema de la GUI con colores, fuentes y configuraciones de espaciado
- Agregar función para crear formularios comunes con manejo de errores y envío
- Agregar menú lateral con navegación y destinos configurables
- Agregar componentes para la creación de páginas y vistas en la aplicación
- Mejorar la pantalla de clubes con un formulario para crear nuevos clubes y una estructura de contenido más clara
- Actualizar la pantalla de inicio para incluir un subtitulo y mejorar la estructura de controles
- Refactorizar la pantalla de login para usar un formulario y mejorar la estructura de la vista
- Refactorizar la pantalla de registro para utilizar un formulario y mejorar la estructura de la vista
- Agregar acción para revisar workflows de GitHub Actions en la configuración de pre-commit
- Agregar acción para verificar linting en el Makefile
- Agregar configuración de flet y actualizar dependencias en pyproject.toml
- Actualizar rutas de la base de datos y logs en RUNBOOK.md
- Agregar acciónlint-py como dependencia en uv.lock
- Agregar revisión de workflows con actionlint en MainAction.yml
- Agregar workflow SpikeBuild para pruebas de compilación con flet
- Agregar workflow TituloPR para validar títulos de PR según Conventional Commits

### Corregido

- Actualizar referencia en comentario del script de inicialización de la base de datos
- Actualizar ruta del archivo de logs en la documentación de la arquitectura
- Actualizar ruta del archivo de logs en la documentación de errores
- Agregar comentario aclaratorio sobre la entidad temporal en el registro de entrenadores
- Mejorar la documentación de rutas y reorganizar la estructura de directorios para datos del usuario
- Agregar comentario aclaratorio sobre el uso de parámetros en la consulta de jugadores
- Crear directorio para la base de datos si no existe al iniciar la interfaz gráfica
- Ajustar configuración de build y excluir archivos innecesarios en la aplicación
