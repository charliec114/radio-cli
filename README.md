# Radio CLI

Un reproductor de radio en línea de comandos con interfaz interactiva.

## Características

- Interfaz interactiva con navegación por teclado
- Soporte para múltiples estaciones de radio
- Reproducción de audio con mpv
- Fácil configuración de estaciones mediante archivo JSON
- Colores en la terminal para mejor experiencia visual

## Requisitos

- bash
- jq
- mpv

## Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/tu-usuario/radio-cli.git
cd radio-cli
```

2. Haz el script ejecutable:
```bash
chmod +x radio.sh
```

3. Instala las dependencias (el script intentará instalarlas automáticamente si no están presentes):
```bash
# En sistemas basados en Debian/Ubuntu
sudo apt install jq mpv

# En sistemas basados en RedHat/Fedora
sudo dnf install jq mpv

# En sistemas basados en Arch Linux
sudo pacman -S jq mpv
```

## Uso

1. Ejecuta el script:
```bash
./radio.sh
```

2. Navega por las estaciones usando las flechas arriba/abajo
3. Presiona Enter para reproducir la estación seleccionada
4. Presiona 'q' para salir

## Configuración

Las estaciones de radio se configuran en el archivo `radios.json`. El formato es el siguiente:

```json
[
    { "title": "Nombre de la estación", "url": "URL de la estación" },
    { "title": "Otra estación", "url": "URL de la otra estación" }
]
```

## Controles

- ↑/↓: Navegar entre estaciones
- Enter: Reproducir/Detener la estación seleccionada
- q: Salir del programa

## Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue o envía un pull request.

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.