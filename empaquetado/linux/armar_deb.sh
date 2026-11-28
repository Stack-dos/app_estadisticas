#!/usr/bin/env bash
# Arma el .deb de Linux (US-109, AC9) a partir de la carpeta que genera "flet build linux".
# Uso (desde la raiz del repo): empaquetado/linux/armar_deb.sh <version sin la v> <carpeta de flet build> <carpeta de salida>
#   empaquetado/linux/armar_deb.sh 0.1.0 build/linux dist
#
# Estructura del paquete:
#   /opt/statspro/                      la app (ejecutable StatsPro, bibliotecas y Python empaquetado)
#   /usr/bin/statspro                   enlace al ejecutable: se abre con "statspro" desde la terminal
#   /usr/share/applications/            acceso directo en el menu del escritorio
#   /usr/share/icons/hicolor/scalable/  icono del acceso directo
# Desinstalar (apt remove statspro) no borra ~/.statspro/: los datos del usuario quedan.
set -euo pipefail

VERSION="$1"
CARPETA_APP="$2"
SALIDA="$3"
AQUI="$(cd "$(dirname "$0")" && pwd)"

# Debian ordena "0.1.0-rc.1" DESPUES de "0.1.0" (el guion separa la revision del paquete).
# Con "~" va antes: 0.1.0~rc.1 < 0.1.0, asi la version final reemplaza al pre-release al instalarla.
VERSION_DEB="${VERSION/-/\~}"

PAQUETE="$(mktemp -d)"
trap 'rm -rf "$PAQUETE"' EXIT
chmod 755 "$PAQUETE"  # mktemp la crea en 700, y esos permisos pasarian a la raiz del paquete

mkdir -p "$PAQUETE/DEBIAN" "$PAQUETE/opt/statspro" "$PAQUETE/usr/bin" \
         "$PAQUETE/usr/share/applications" "$PAQUETE/usr/share/icons/hicolor/scalable/apps"

cp -a "$CARPETA_APP/." "$PAQUETE/opt/statspro/"
ln -s /opt/statspro/StatsPro "$PAQUETE/usr/bin/statspro"
install -m 644 "$AQUI/statspro.desktop" "$PAQUETE/usr/share/applications/statspro.desktop"
install -m 644 "$AQUI/../../src/assets/icon.svg" \
               "$PAQUETE/usr/share/icons/hicolor/scalable/apps/statspro.svg"

# libgtk-3-0t64 es el nombre desde Ubuntu 24.04 / Debian 13; libgtk-3-0 el de antes
cat > "$PAQUETE/DEBIAN/control" <<EOF
Package: statspro
Version: $VERSION_DEB
Section: misc
Priority: optional
Architecture: amd64
Depends: libgtk-3-0t64 | libgtk-3-0
Maintainer: StatsPro <nicopinera@users.noreply.github.com>
Homepage: https://github.com/nicopinera/app_estadisticas
Description: Estadisticas de basquet para entrenadores
 Aplicacion de escritorio para cargar y analizar estadisticas de partidos de basquet,
 sin conexion a internet. Los datos se guardan en ~/.statspro/.
EOF

mkdir -p "$SALIDA"
DEB="$SALIDA/statspro_${VERSION_DEB}_amd64.deb"
# --root-owner-group: los archivos quedan a nombre de root, no del usuario del runner
dpkg-deb --build --root-owner-group "$PAQUETE" "$DEB"
dpkg-deb --info "$DEB"
echo "Listo: $DEB"
