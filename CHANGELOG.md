# Changelog

Qué trae cada versión de StatsPro, contado para quien usa la app. La más nueva va arriba.

La numeración es propia del proyecto: el primer número sube al cerrar cada etapa grande, el segundo con cada
grupo de funciones nuevas y el tercero con cada corrección. **Ninguna versión borra ni rompe los datos que ya
cargaste**: actualizar es instalar la nueva encima de la anterior.

## [1.0.0] - 2026-11-28

La primera versión de StatsPro. Es una aplicación de escritorio para que un entrenador de básquet registre los
partidos de su club y tenga a mano las estadísticas de su plantel, sin planillas sueltas ni internet. Se instala en
Windows o en Linux, no necesita tener Python y guarda todo en tu computadora.

### Tu cuenta y tus clubes

Te creás una cuenta con nombre, email y contraseña. Si marcás **"Recordarme"**, la próxima vez que abras la app
entrás directo, con el mismo club con el que estabas trabajando. Podés tener más de un club propio y elegir con cuál
trabajar; el club activo se ve siempre en la barra de arriba. Los clubes rivales se crean solos cuando cargás un
partido contra ellos, y si escribiste mal un nombre lo podés corregir o borrar desde "Mis clubes".

### El plantel

En "Jugadores" está tu plantel, con un buscador que filtra mientras escribís. Podés agregar jugadores, editarlos y
darlos de baja con su fecha. Si querés sumar a alguien que ya existe, la app te avisa en qué club está, y si quedó
sin club te ofrece sumarlo en vez de crearlo dos veces. También podés ver a todos los jugadores de todos los clubes.

### Torneos, inscripciones y listas de buena fe

En "Torneos" cargás las competencias con sus categorías (U13, U15, Primera...), inscribís a tu club y armás la lista
de buena fe de cada inscripción. Al inscribirte, todo el plantel puede entrar a la lista de una vez; después podés
sumar o sacar jugadores de a varios. Si alguno no puede entrar, la app te dice por qué.

### Cargar un partido

Un asistente de tres pasos:

1. **Datos del partido:** torneo, fecha, estadio, rival y si jugaste de local o de visitante.
2. **Boxscore:** elegís hasta 12 convocados de tu lista y completás la planilla, que se maneja como un Excel. Los
   puntos y los totales del equipo se calculan solos. Del rival podés cargar solo el resultado, sus totales o el
   boxscore de cada jugador. Los puntos por cuarto son opcionales.
3. **Confirmar:** un resumen con el marcador antes de guardar. Te avisa si cargaste menos de 5 jugadores o si el
   partido parece repetido.

Si algo está mal, la planilla marca el jugador y la columna con el error, y no se guarda nada a medias.

### Ver tus partidos y tus números

En "Partidos" están todos los partidos del club, con el resultado y si ganaste o perdiste. Cada uno se abre en su
propia pantalla, con el marcador, los puntos por cuarto, los totales de cada equipo y el boxscore completo. Desde ahí
se puede **editar** o **eliminar**. La pantalla de inicio muestra el último partido y los líderes del club en
promedio de puntos, rebotes y asistencias.

### Ayuda y avisos

- El botón **"Guía"** del menú abre un manual corto de uso.
- Al abrir, la app se fija si hay una **versión nueva** y, si la hay, te ofrece descargarla. Lo hace como mucho una
  vez por día y, si no hay internet, sigue sin avisar.
- Si algo falla, la app te muestra un mensaje claro y guarda el detalle en un archivo de registro para poder
  reportarlo.

### Lo que todavía no hace

- La sesión recordada no vence: cualquiera que use tu usuario de la computadora entra sin contraseña.
- No se pueden cargar partidos entre dos clubes que no son tuyos.
- No se puede renombrar ni borrar un club propio.
- El instalador de Windows no está firmado: la primera vez Windows muestra "Windows protegió su PC". Se abre con
  _Más información → Ejecutar de todas formas_.

### Quiénes la hicieron

- Nicolas Piñera ([nicopinera](https://github.com/nicopinera))
- Marcos Battigane ([marcosbattigane](https://github.com/marcosbattigane))
