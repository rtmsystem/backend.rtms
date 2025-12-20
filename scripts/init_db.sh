#!/bin/bash

# Script para inicializar la base de datos

echo "🔧 Esperando a que PostgreSQL esté listo..."
sleep 5

echo "📦 Ejecutando migraciones..."
python manage.py makemigrations
python manage.py migrate

echo "✅ Base de datos inicializada correctamente"

