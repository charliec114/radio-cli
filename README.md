# Radio CLI

Reproductor de radio en línea de comandos con interfaz ncurses implementada en Python.

## Características técnicas

- **Interfaz**: ncurses con manejo de colores y caracteres Unicode
- **Sistema de scroll**: Paginación automática para listas extensas
- **Control de volumen**: IPC con mpv mediante sockets Unix
- **Gestión de procesos**: Control de procesos mpv con manejo de señales
- **Validación de terminal**: Verificación de dimensiones mínimas (60x20)
- **Manejo de errores**: Try-catch robusto para operaciones curses
- **Adaptabilidad**: Cálculo dinámico de layouts según dimensiones de terminal

## Requisitos del sistema

- **Python**: 3.6+ (requiere `curses`, `subprocess`, `os`, `signal`, `typing`)
- **mpv**: Reproductor multimedia con soporte para `--input-ipc-server`
- **Terminal**: Soporte para ncurses y caracteres Unicode
- **Sistema**: Linux, macOS, WSL (sockets Unix para IPC)

**Nota sobre versiones:**
- `typing` está disponible desde Python 3.5+
- `curses` tiene mejor soporte desde Python 3.6+
- **Versión mínima recomendada: Python 3.6+**

## Instalación

```bash
git clone https://github.com/tu-usuario/radio-cli.git
cd radio-cli
chmod +x radio.py
```

### Dependencias

#### Dependencias del sistema
```bash
# Ubuntu/Debian
sudo apt install mpv

# Fedora/RHEL
sudo dnf install mpv

# Arch Linux
sudo pacman -S mpv

# macOS
brew install mpv
```

#### Dependencias de Python
El proyecto utiliza solo la biblioteca estándar de Python, por lo que **no se requieren paquetes externos** de pip.

**Verificación de dependencias:**
```bash
# Verificar que curses esté disponible
python3 -c "import curses; print('✓ curses disponible')"

# Verificar versión de Python
python3 --version
```

**Nota:** Si estás en Windows, `curses` no está disponible por defecto. Considera usar WSL o una alternativa como `windows-curses`.

### Archivo requirements.txt

El archivo `requirements.txt` está incluido por convención, pero **no contiene dependencias externas** ya que todas las librerías utilizadas están incluidas en Python 3.6+:

- `curses` - Interfaz ncurses
- `json` - Procesamiento de JSON
- `subprocess` - Ejecución de procesos externos
- `os` - Operaciones del sistema operativo
- `signal` - Manejo de señales del sistema
- `sys` - Funciones del sistema Python

## Uso

```bash
./radio.py
```

### Controles de navegación

| Tecla | Función |
|-------|---------|
| `↑` | Estación anterior |
| `↓` | Estación siguiente |
| `←` | Volumen -10% |
| `→` | Volumen +10% |
| `Enter` | Play/Pause |
| `q` | Salir |

## Arquitectura del código

### Clase principal: `RadioCLI`

```python
class RadioCLI:
    def __init__(self):
        self.selected = 0          # Índice de estación seleccionada
        self.playing = False       # Estado de reproducción
        self.mpv_pid = None       # PID del proceso mpv
        self.volume = 50          # Nivel de volumen (0-100)
        self.current_station = "" # Estación actualmente reproduciendo
        self.radios = []          # Lista de estaciones del JSON
        self.scroll_offset = 0    # Offset para paginación
        self.screen = None        # Objeto curses screen
```

### Sistema de scroll

```python
# Cálculo de estaciones visibles
max_visible = stations_height - 3
visible_radios = self.radios[self.scroll_offset:self.scroll_offset + max_visible]

# Ajuste automático del scroll
if self.selected < self.scroll_offset:
    self.scroll_offset = self.selected
```

### Control de volumen IPC

```python
# Inicio de mpv con socket IPC
mpv --volume="$volume" --input-ipc-server=/tmp/mpv-socket "$url"

# Ajuste de volumen en tiempo real
echo "volume $volume" | socat - /tmp/mpv-socket
```

## Estructura del archivo JSON

```json
[
    {
        "title": "Nombre de la estación",
        "url": "URL del stream"
    }
]
```

### Formatos de URL soportados

- **HTTP/HTTPS**: `https://stream.radio.com/audio.mp3`
- **HLS**: `https://stream.radio.com/playlist.m3u8`
- **RTMP**: `rtmp://stream.radio.com/live`
- **Local**: `file:///ruta/al/archivo.mp3`

## Implementación técnica

### Manejo de curses

```python
# Configuración inicial
self.screen = curses.initscr()
curses.noecho()
curses.cbreak()
curses.curs_set(0)
self.screen.keypad(True)

# Paleta de colores
curses.start_color()
curses.use_default_colors()
curses.init_pair(1, curses.COLOR_RED, -1)
curses.init_pair(2, curses.COLOR_GREEN, -1)
```

### Validación de límites de pantalla

```python
def draw_box(self, y: int, x: int, height: int, width: int, title: str = ""):
    screen_height, screen_width = self.screen.getmaxyx()
    
    # Validar que el marco quepa en la pantalla
    if x < 0 or y < 0 or x + width > screen_width or y + height > screen_height:
        return
```

### Gestión de procesos mpv

```python
def play_station(self):
    if self.playing:
        os.kill(self.mpv_pid, signal.SIGTERM)
        self.playing = False
    else:
        process = subprocess.Popen([
            'mpv', '--volume=' + str(self.volume),
            '--input-ipc-server=/tmp/mpv-socket',
            '--no-video', '--quiet', radio['url']
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.mpv_pid = process.pid
```

## Rendimiento y escalabilidad

### Optimizaciones implementadas

- **Renderizado selectivo**: Solo se redibuja cuando es necesario
- **Scroll eficiente**: Paginación O(1) para navegación
- **Gestión de memoria**: Limpieza automática de procesos y sockets
- **Validación de límites**: Prevención de errores curses

### Límites de rendimiento

- **Estaciones**: Teóricamente ilimitadas (prácticamente hasta 10,000+)
- **Memoria**: O(n) donde n = número de estaciones
- **CPU**: O(1) para navegación, O(n) para renderizado inicial

## Manejo de errores

### Errores comunes y soluciones

```python
# Error de terminal pequeña
if width < 60 or height < 20:
    self.screen.addstr(0, 0, "Terminal muy pequeña. Necesitas al menos 60x20 caracteres.")
    return

# Error de curses
try:
    self.screen.addch(y, x, curses.ACS_ULCORNER)
except curses.error:
    pass  # Continuar sin crashear
```

### Recuperación de errores

- **Proceso mpv muerto**: Reinicio automático al intentar reproducir
- **Socket corrupto**: Limpieza automática al salir
- **Terminal corrupta**: Restauración automática con `curses.endwin()`

## Configuración avanzada

### Variables de entorno

```bash
# Tamaño mínimo de terminal
export RADIO_CLI_MIN_WIDTH=60
export RADIO_CLI_MIN_HEIGHT=20

# Socket IPC personalizado
export RADIO_CLI_SOCKET=/tmp/mi-radio-socket
```

### Personalización de colores

```python
# Modificar en la función run()
curses.init_pair(1, curses.COLOR_RED, -1)      # Error
curses.init_pair(2, curses.COLOR_GREEN, -1)    # Éxito
curses.init_pair(3, curses.COLOR_YELLOW, -1)   # Advertencia
curses.init_pair(4, curses.COLOR_CYAN, -1)     # Información
```

## Testing y debugging

### Verificación de dependencias

```bash
# Verificar que curses esté disponible
python3 -c "import curses; print('✓ curses disponible')"

# Verificar versión de Python
python3 --version

# Verificar que mpv esté instalado
which mpv
mpv --version

# Verificar JSON
python3 -c "import json; json.load(open('radios.json')); print('✓ JSON válido')"
```

### Modo debug

```python
# Comentar esta línea para ver logs de mpv
# stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL

# Agregar logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Verificación de funcionalidad

```bash
# Ejecutar con verificación de dependencias
python3 -c "
import sys
import curses
import json
import subprocess
import os
import signal

print('✓ Todas las dependencias están disponibles')
print(f'✓ Python {sys.version}')
print('✓ Radio CLI listo para ejecutar')
"
```

## Contribución

### Estructura del proyecto

```
radio-cli/
├── radio.py          # Implementación principal
├── radios.json       # Configuración de estaciones
├── README.md         # Documentación técnica
└── requirements.txt  # Dependencias Python (solo biblioteca estándar)
```

### Dependencias del proyecto

**Importante:** Este proyecto utiliza **solo la biblioteca estándar de Python**. No se requieren paquetes externos de pip.

**Librerías utilizadas:**
- `curses` - Interfaz ncurses (incluida en Python 3.6+)
- `json` - Procesamiento de JSON (incluida en Python 3.6+)
- `subprocess` - Ejecución de procesos (incluida en Python 3.6+)
- `os` - Operaciones del sistema (incluida en Python 3.6+)
- `signal` - Manejo de señales (incluida en Python 3.6+)
- `sys` - Funciones del sistema (incluida en Python 3.6+)
- `typing` - Anotaciones de tipo (incluida en Python 3.5+, List, Dict, Optional)

**Dependencias del sistema:**
- `mpv` - Reproductor multimedia (instalar via gestor de paquetes)
- Terminal con soporte para ncurses

### Estándares de código

- **PEP 8**: Estilo de código Python
- **Type hints**: Anotaciones de tipo donde sea apropiado
- **Docstrings**: Documentación de funciones y métodos
- **Manejo de errores**: Try-catch para operaciones críticas
- **Sin dependencias externas**: Mantener solo biblioteca estándar

## Licencia

MIT License - Ver archivo `LICENSE`