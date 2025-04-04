#!/bin/bash

# Verificar que jq y mpv estén instalados
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

echo "Elige una estación:"
jq -r '.[] | "\(.title)"' "$json_file" | nl -w2 -s") "

read -p "> " opt
url=$(jq -r ".[$((opt-1))].url" "$json_file")

if [ "$url" != "null" ]; then
  mpv "$url"
else
  echo "Opción inválida"
fi
