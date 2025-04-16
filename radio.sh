#!/bin/bash

# Verificar que jq, mpv y ncurses estén instalados
check_deps() {
  for cmd in jq mpv; do
    if ! command -v "$cmd" &>/dev/null; then
      echo "$cmd no está instalado. Instalándolo..."
      if [ -f /etc/debian_version ]; then
        sudo apt update && sudo apt install -y "$cmd"
      elif [ -f /etc/redhat-release ]; then
        sudo dnf install -y "$cmd"
      elif command -v pacman &>/dev/null; then
        sudo pacman -Sy "$cmd"
      elif command -v zypper &>/dev/null; then
        sudo zypper install -y "$cmd"
      else
        echo "Distribución no soportada para instalar $cmd."
        exit 1
      fi
    fi
  done
}

check_deps

# Leer radios del archivo JSON
json_file="radios.json"
if [ ! -f "$json_file" ]; then
  echo "No se encontró $json_file"
  exit 1
fi

# Función para mostrar la interfaz ncurses
show_interface() {
  # Inicializar ncurses
  clear
  echo -e "\e[1;32m=== Radio CLI ===\e[0m\n"
  
  # Mostrar lista de radios
  echo -e "\e[1;33mEstaciones disponibles:\e[0m\n"
  
  # Obtener y mostrar las radios
  while IFS= read -r title; do
    if [ "$selected" -eq "$i" ]; then
      echo -e "\e[1;32m→ $title\e[0m"
    else
      echo "  $title"
    fi
    ((i++))
  done < <(jq -r '.[].title' "$json_file")
  
  echo -e "\n\e[1;33mControles:\e[0m"
  echo "↑/↓: Navegar"
  echo "Enter: Seleccionar"
  echo "q: Salir"
}

# Variables iniciales
selected=0
playing=false
mpv_pid=""

# Bucle principal
while true; do
  i=0
  show_interface
  
  # Leer tecla
  read -rsn1 input
  
  case "$input" in
    "A") # Flecha arriba
      if [ "$selected" -gt 0 ]; then
        ((selected--))
      fi
      ;;
    "B") # Flecha abajo
      total_radios=$(jq 'length' "$json_file")
      if [ "$selected" -lt $((total_radios-1)) ]; then
        ((selected++))
      fi
      ;;
    "") # Enter
      if [ "$playing" = true ]; then
        kill "$mpv_pid" 2>/dev/null
        playing=false
      fi
      url=$(jq -r ".[$selected].url" "$json_file")
      mpv "$url" &>/dev/null &
      mpv_pid=$!
      playing=true
      ;;
    "q") # Salir
      if [ "$playing" = true ]; then
        kill "$mpv_pid" 2>/dev/null
      fi
      clear
      exit 0
      ;;
  esac
done
