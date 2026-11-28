# ADR-006: Seguridad de Credenciales y Cifrado de Datos

- **Estado**: Aprobado para v0.1 (hashing de contraseñas); Pendiente para v1.0 (cifrado de DB,
  rotación a bcrypt/argon2, lista de contraseñas comprometidas) — ver preguntas abiertas
- **Fecha**: 2026-10-03

## Contexto

Dos momentos distintos del proyecto necesitan decisiones de seguridad: la US-104 (Hito 1, v0.1)
necesita hashear contraseñas antes de guardarlas; la US-403 (Hito 4, v1.0, "Hardening de
Seguridad Local") pide endurecer eso — contraseñas más exigentes, hashing más robusto, lista de
contraseñas comprometidas, y **cifrado de la base de datos local** (hoy el archivo `.db` de
SQLite no está cifrado: cualquiera con acceso al archivo puede leer todos los datos con cualquier
visor de SQLite).

Este ADR en el plan original mezclaba ambas decisiones y tenía una contradicción entre dos
secciones del mismo documento sobre si v0.1 usaba salt fijo o dinámico — ya corregida durante la
revisión de la US-104 (2026-10-03): v0.1 usa salt **dinámico**.

## Alternativas Consideradas

**Para el hashing de contraseñas (v0.1, ya resuelto):**

- **`hashlib.pbkdf2_hmac`/SHA-256 con salt dinámico:** disponible en la librería estándar de
  Python, sin dependencias nuevas; lento a propósito (iteraciones configurables) pero menos que
  las alternativas dedicadas.
- **`bcrypt`/`argon2-cffi`:** librerías dedicadas a hashing de contraseñas, diseñadas para ser
  deliberadamente lentas (y, en el caso de Argon2, costosas en memoria) — más resistentes a
  fuerza bruta masiva, a costa de una dependencia binaria nueva.

**Para el cifrado de la base de datos (v1.0, pendiente):**

- **SQLCipher:** extensión de SQLite que cifra el archivo `.db` completo de forma transparente,
  reemplazando el módulo `sqlite3` estándar por un binding compatible (ej. `sqlcipher3`). Requiere
  validar que ese binding compile/funcione en todas las plataformas objetivo.
- **No cifrar el archivo de DB, confiar en el cifrado del disco del sistema operativo
  (BitLocker/FileVault/LUKS):** más simple de implementar (no cambia nada en el código), pero deja
  de proteger el dato si el atacante ya tiene la sesión del usuario desbloqueada, o si se copia el
  archivo `.db` a otra máquina sin cifrado de disco.

## Decisión Tomada

**v0.1 (ya implementado en US-104):** `pbkdf2_hmac` con salt dinámico (uno distinto por usuario,
generado con `os.urandom` al registrarse, guardado junto al hash). Sin dependencias nuevas,
suficiente para la amenaza real de v0.1 (una app local, de un usuario, sin servicio expuesto a
internet).

**v1.0 (US-403, pendiente — ver preguntas abiertas):** migrar el hashing a `bcrypt` o `argon2-cffi`
(a definir cuál cuando se llegue a esa US), y **adoptar SQLCipher** para cifrar la base completa —
con la salvedad explícita de la primera pregunta abierta.

## Preguntas abiertas (a resolver entre nosotros antes de cerrar la parte de v1.0)

> 1. **Viabilidad de SQLCipher en las 4 plataformas de la US-404 (Windows, Linux, macOS y
>    Android vía Flet):** se confirma la intención de usar SQLCipher, pero **hay que validar antes
>    de comprometerse del todo** que el binding elegido (ej. `sqlcipher3-binary` o equivalente)
>    tenga wheels/soporte real para Android empaquetado con Flet — es la plataforma más atípica de
>    las cuatro y la que más probablemente dé problemas. Si no es viable en Android, hay que
>    decidir si esa plataforma queda sin cifrado de DB (con una nota explícita de limitación) o si
>    se busca una alternativa específica para ese caso.
> 2. **Fuente de la lista de contraseñas comprometidas (AC2 de la US-403):** todavía no está
>    definido de dónde sale esa lista (ej. un dump público tipo las listas "top N" derivadas de
>    _Have I Been Pwned_, o alguna otra fuente). Queda pendiente de definir cuando se llegue a esa
>    US — también condiciona el AC4 (CI valida versión y checksum de esa lista en cada PR), que
>    no se puede detallar sin saber antes de dónde sale el archivo.
> 3. **Cuál de bcrypt o argon2-cffi para v1.0:** el AC5 de la US-403 acepta cualquiera de los dos;
>    no es una decisión urgente hoy, se puede resolver en el momento de implementar esa US.

## Ventajas y Desventajas

### Ventajas (v0.1, ya vigente)

- Sin dependencias nuevas: `pbkdf2_hmac` es parte de la librería estándar de Python.
- Salt dinámico por usuario: dos usuarios con la misma contraseña nunca comparten el mismo hash
  guardado, y un salt filtrado no sirve para atacar a todos los usuarios a la vez.

### Desventajas / riesgos (v0.1 y v1.0)

- `pbkdf2_hmac` es menos resistente a fuerza bruta con hardware dedicado que `bcrypt`/`argon2` —
  aceptado como riesgo conocido para v0.1, a corregir en v1.0.
- El archivo `.db` no está cifrado hoy: cualquiera con acceso al archivo (robo de la
  computadora, copia del archivo) puede leer todos los datos sin necesidad de ninguna contraseña
  de la aplicación — este es justamente el problema que SQLCipher busca resolver en v1.0.
- Adoptar SQLCipher agrega una dependencia binaria multiplataforma, con el riesgo de
  compatibilidad ya marcado en la pregunta abierta 1 — no es una decisión sin costo de
  mantenimiento.
