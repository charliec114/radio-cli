#!/usr/bin/env python3
"""
Radio CLI - Reproductor de radio en línea de comandos con interfaz curses
"""

import curses
import json
import subprocess
import os
import signal
import sys
from typing import List, Dict, Optional

class RadioCLI:
    def __init__(self):
        self.selected = 0
        self.playing = False
        self.mpv_pid = None
        self.volume = 50
        self.current_station = ""
        self.radios = []
        self.screen = None
        self.scroll_offset = 0  # Para el scroll de estaciones
        
    def load_radios(self, json_file: str = "radios.json") -> bool:
        """Cargar estaciones de radio desde archivo JSON"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.radios = json.load(f)
            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error cargando {json_file}: {e}")
            return False
    
    def draw_box(self, y: int, x: int, height: int, width: int, title: str = ""):
        """Dibujar un marco con título"""
        # Validar límites de la pantalla
        screen_height, screen_width = self.screen.getmaxyx()
        
        # Asegurar que el marco quepa en la pantalla
        if x < 0 or y < 0 or x + width > screen_width or y + height > screen_height:
            return
        
        try:
            # Esquinas
            self.screen.addch(y, x, curses.ACS_ULCORNER)
            self.screen.addch(y, x + width - 1, curses.ACS_URCORNER)
            self.screen.addch(y + height - 1, x, curses.ACS_LLCORNER)
            self.screen.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)
            
            # Líneas horizontales
            for i in range(x + 1, x + width - 1):
                if i < screen_width:
                    self.screen.addch(y, i, curses.ACS_HLINE)
                    self.screen.addch(y + height - 1, i, curses.ACS_HLINE)
            
            # Líneas verticales
            for i in range(y + 1, y + height - 1):
                if i < screen_height:
                    self.screen.addch(i, x, curses.ACS_VLINE)
                    self.screen.addch(i, x + width - 1, curses.ACS_VLINE)
            
            # Título centrado
            if title:
                title_x = x + (width - len(title)) // 2
                if title_x >= x and title_x + len(title) < x + width:
                    self.screen.addstr(y, title_x, f" {title} ")
        except curses.error:
            # Si hay algún error, simplemente continuar
            pass
    
    def draw_progress_bar(self, y: int, x: int, width: int, percent: int, label: str = ""):
        """Dibujar barra de progreso para el volumen"""
        # Validar límites de la pantalla
        screen_height, screen_width = self.screen.getmaxyx()
        
        if y < 0 or y >= screen_height or x < 0 or x + width > screen_width:
            return
        
        try:
            filled = int(width * percent / 100)
            
            # Etiqueta
            if label:
                self.screen.addstr(y, x, f"{label}: ")
                x += len(label) + 2
            
            # Barra
            self.screen.addstr(y, x, "[")
            for i in range(width):
                if i < filled:
                    self.screen.addch(y, x + 1 + i, '█', curses.color_pair(2))
                else:
                    self.screen.addch(y, x + 1 + i, '░', curses.color_pair(7))
            self.screen.addstr(y, x + width + 1, f"] {percent}%")
        except curses.error:
            # Si hay algún error, simplemente continuar
            pass
    
    def show_interface(self):
        """Mostrar la interfaz principal"""
        self.screen.clear()
        
        # Obtener dimensiones
        height, width = self.screen.getmaxyx()
        
        # Verificar tamaño mínimo de terminal
        if width < 60 or height < 20:
            self.screen.addstr(0, 0, "Terminal muy pequeña. Necesitas al menos 60x20 caracteres.", curses.color_pair(1))
            self.screen.addstr(1, 0, f"Tu terminal: {width}x{height}", curses.color_pair(3))
            self.screen.addstr(2, 0, "Redimensiona la terminal y presiona cualquier tecla...", curses.color_pair(3))
            self.screen.refresh()
            self.screen.getch()
            return
        
        # Título principal con línea decorativa
        title = "🎵 RADIO CLI 🎵"
        title_x = max(0, (width - len(title)) // 2)
        self.screen.addstr(1, title_x, title, curses.color_pair(4) | curses.A_BOLD)
        
        # Línea decorativa debajo del título
        line = "─" * (len(title) + 4)
        line_x = max(0, (width - len(line)) // 2)
        self.screen.addstr(2, line_x, line, curses.color_pair(4))
        
        # Panel principal de estaciones (más ancho y centrado)
        stations_width = min(70, width - 10)
        stations_x = max(2, (width - stations_width) // 2)
        stations_height = min(height - 12, height - 8)
        
        # Marco para estaciones
        # Mostrar estaciones con mejor formato y scroll
        start_y = 6
        max_visible = stations_height - 3
        
        # Calcular qué estaciones mostrar basado en el scroll
        visible_radios = self.radios[self.scroll_offset:self.scroll_offset + max_visible]
        
        for i, radio in enumerate(visible_radios):
            if start_y + i < height - 1:
                y_pos = start_y + i
                actual_index = self.scroll_offset + i
                
                # Número de estación
                station_num = f"{actual_index + 1:2d}."
                self.screen.addstr(y_pos, stations_x + 2, station_num, curses.color_pair(3))
                
                if actual_index == self.selected:
                    # Estación seleccionada
                    self.screen.addstr(y_pos, stations_x + 6, "▶ ", curses.color_pair(2))
                    self.screen.addstr(y_pos, stations_x + 8, radio['title'], curses.color_pair(2) | curses.A_BOLD)
                    
                    # Mostrar URL de la estación seleccionada
                    url_y = y_pos + 1
                    if url_y < height - 1 and url_y < stations_height + 3:
                        url_display = radio['url'][:stations_width - 10] + "..." if len(radio['url']) > stations_width - 10 else radio['url']
                        self.screen.addstr(url_y, stations_x + 8, url_display, curses.color_pair(6))
                else:
                    # Estación no seleccionada
                    self.screen.addstr(y_pos, stations_x + 6, "  ")
                    self.screen.addstr(y_pos, stations_x + 8, radio['title'], curses.color_pair(7))
        
        # Mostrar indicadores de scroll
        if self.scroll_offset > 0:
            # Indicador de que hay más arriba
            scroll_up_y = start_y - 1
            if scroll_up_y >= 0:
                self.screen.addstr(scroll_up_y, stations_x + stations_width // 2 - 3, "↑ ↑ ↑", curses.color_pair(3))
        
        if self.scroll_offset + max_visible < len(self.radios):
            # Indicador de que hay más abajo
            scroll_down_y = start_y + max_visible
            if scroll_down_y < height - 1:
                self.screen.addstr(scroll_down_y, stations_x + stations_width // 2 - 3, "↓ ↓ ↓", curses.color_pair(3))
        
        # Mostrar información de scroll en el título del marco
        if len(self.radios) > max_visible:
            scroll_info = f"📻 ESTACIONES ({len(self.radios)}) - Scroll {self.scroll_offset + 1}-{min(self.scroll_offset + max_visible, len(self.radios))}"
            self.draw_box(4, stations_x, stations_height, stations_width, scroll_info)
        else:
            self.draw_box(4, stations_x, stations_height, stations_width, f"📻 ESTACIONES ({len(self.radios)})")
        
        # Panel de controles y estado (abajo, centrado)
        controls_width = min(60, width - 10)
        controls_x = max(2, (width - controls_width) // 2)
        controls_y = min(4 + stations_height + 1, height - 10)
        
        # Asegurar que el panel de controles quepa en la pantalla
        if controls_y + 8 < height:
            self.draw_box(controls_y, controls_x, 8, controls_width, "🎮 CONTROLES Y ESTADO")
            
            # Primera fila: Controles principales
            self.screen.addstr(controls_y + 1, controls_x + 2, "↑/↓: Navegar", curses.color_pair(3))
            self.screen.addstr(controls_y + 1, controls_x + 25, "←/→: Volumen", curses.color_pair(3))
            self.screen.addstr(controls_y + 1, controls_x + 45, "Enter: Play/Pause", curses.color_pair(3))
            
            # Segunda fila: Estado de reproducción
            self.screen.addstr(controls_y + 2, controls_x + 2, "Estado:")
            if self.playing:
                self.screen.addstr(controls_y + 2, controls_x + 10, "▶ Reproduciendo", curses.color_pair(2))
            else:
                self.screen.addstr(controls_y + 2, controls_x + 10, "⏸ Pausado", curses.color_pair(1))
            
            # Tercera fila: Estación actual
            self.screen.addstr(controls_y + 3, controls_x + 2, "Estación:")
            if self.current_station:
                self.screen.addstr(controls_y + 3, controls_x + 12, self.current_station, curses.color_pair(6))
            else:
                self.screen.addstr(controls_y + 3, controls_x + 12, "Ninguna seleccionada", curses.color_pair(7))
            
            # Cuarta fila: Volumen con barra integrada
            self.screen.addstr(controls_y + 4, controls_x + 2, "Volumen:")
            volume_bar_width = min(30, controls_width - 15)
            volume_bar_x = controls_x + 12
            self.draw_progress_bar(controls_y + 4, volume_bar_x, volume_bar_width, self.volume, "")
            
            # Quinta fila: Información adicional
            self.screen.addstr(controls_y + 5, controls_x + 2, f"Estación {self.selected + 1} de {len(self.radios)}", curses.color_pair(3))
            self.screen.addstr(controls_y + 5, controls_x + 35, "q: Salir", curses.color_pair(3))
            
            # Línea separadora
            separator_y = controls_y + 6
            if separator_y < height - 1:
                separator_line = "─" * (controls_width - 4)
                self.screen.addstr(separator_y, controls_x + 2, separator_line, curses.color_pair(4))
                
                # Información de ayuda
                help_text = "💡 Usa las flechas para navegar y ajustar volumen"
                help_x = max(0, (width - len(help_text)) // 2)
                if separator_y + 1 < height - 1:
                    self.screen.addstr(separator_y + 1, help_x, help_text, curses.color_pair(3))
        
        self.screen.refresh()
    
    def adjust_volume(self, change: int):
        """Ajustar volumen"""
        new_volume = self.volume + change
        if 0 <= new_volume <= 100:
            self.volume = new_volume
            
            # Ajustar volumen en mpv si está reproduciendo
            if self.playing and self.mpv_pid:
                try:
                    # Usar mpv --input-ipc-server para control remoto
                    subprocess.run([
                        'mpv', '--input-ipc-server=/tmp/mpv-socket',
                        '--volume=' + str(self.volume)
                    ], check=False)
                except:
                    pass
    
    def play_station(self):
        """Reproducir o pausar estación"""
        if self.playing:
            # Detener reproducción
            if self.mpv_pid:
                try:
                    os.kill(self.mpv_pid, signal.SIGTERM)
                except:
                    pass
            self.playing = False
            self.current_station = ""
            self.mpv_pid = None
        else:
            # Iniciar reproducción
            if self.radios:
                radio = self.radios[self.selected]
                self.current_station = radio['title']
                
                try:
                    # Iniciar mpv en segundo plano
                    process = subprocess.Popen([
                        'mpv', '--volume=' + str(self.volume),
                        '--input-ipc-server=/tmp/mpv-socket',
                        '--no-video', '--quiet',
                        radio['url']
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.mpv_pid = process.pid
                    self.playing = True
                except Exception as e:
                    self.current_station = f"Error: {e}"
    
    def run(self):
        """Ejecutar la aplicación principal"""
        try:
            # Configurar curses
            self.screen = curses.initscr()
            curses.noecho()
            curses.cbreak()
            curses.curs_set(0)
            self.screen.keypad(True)
            
            # Configurar colores
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_RED, -1)      # Rojo
            curses.init_pair(2, curses.COLOR_GREEN, -1)    # Verde
            curses.init_pair(3, curses.COLOR_YELLOW, -1)   # Amarillo
            curses.init_pair(4, curses.COLOR_CYAN, -1)     # Cyan
            curses.init_pair(6, curses.COLOR_MAGENTA, -1)  # Magenta
            curses.init_pair(7, curses.COLOR_WHITE, -1)    # Blanco
            
            # Bucle principal
            while True:
                self.show_interface()
                
                # Leer tecla
                key = self.screen.getch()
                
                if key == ord('q'):
                    break
                elif key == curses.KEY_UP:
                    if self.selected > 0:
                        self.selected -= 1
                        # Ajustar scroll si es necesario
                        if self.selected < self.scroll_offset:
                            self.scroll_offset = self.selected
                    elif len(self.radios) > 0:
                        # Ir a la última estación (wrap around)
                        self.selected = len(self.radios) - 1
                        # Ajustar scroll para mostrar la última estación
                        screen_height, _ = self.screen.getmaxyx()
                        stations_height = min(screen_height - 12, screen_height - 8)
                        max_visible = stations_height - 3
                        if len(self.radios) > max_visible:
                            self.scroll_offset = max(0, len(self.radios) - max_visible)
                elif key == curses.KEY_DOWN:
                    if self.selected < len(self.radios) - 1:
                        self.selected += 1
                        # Ajustar scroll si es necesario
                        screen_height, _ = self.screen.getmaxyx()
                        stations_height = min(screen_height - 12, screen_height - 8)
                        max_visible = stations_height - 3
                        if self.selected >= self.scroll_offset + max_visible:
                            self.scroll_offset = self.selected - max_visible + 1
                    elif len(self.radios) > 0:
                        # Ir a la primera estación (wrap around)
                        self.selected = 0
                        self.scroll_offset = 0
                elif key == curses.KEY_LEFT:
                    self.adjust_volume(-10)
                elif key == curses.KEY_RIGHT:
                    self.adjust_volume(10)
                elif key == ord('\n') or key == ord(' '):  # Enter o Espacio
                    self.play_station()
                
        except KeyboardInterrupt:
            pass
        finally:
            # Limpiar
            if self.playing and self.mpv_pid:
                try:
                    os.kill(self.mpv_pid, signal.SIGTERM)
                except:
                    pass
            
            # Limpiar socket temporal
            try:
                os.remove('/tmp/mpv-socket')
            except:
                pass
            
            # Restaurar terminal
            curses.nocbreak()
            self.screen.keypad(False)
            curses.echo()
            curses.endwin()

def main():
    """Función principal"""
    # Verificar dependencias
    try:
        subprocess.run(['mpv', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: mpv no está instalado. Instálalo primero.")
        print("Ubuntu/Debian: sudo apt install mpv")
        print("Fedora/RHEL: sudo dnf install mpv")
        print("Arch: sudo pacman -S mpv")
        sys.exit(1)
    
    # Crear y ejecutar aplicación
    radio = RadioCLI()
    if radio.load_radios():
        radio.run()
    else:
        print("Error: No se pudo cargar el archivo radios.json")
        sys.exit(1)

if __name__ == "__main__":
    main()
