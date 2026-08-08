#!/usr/bin/env bash
#
# deploy/backup_db.sh
# Respaldo diario de la base de datos MySQL de Madera & Vida.
#
# Instalacion:
#   sudo cp deploy/backup_db.sh /usr/local/bin/maderavida-backup
#   sudo chmod +x /usr/local/bin/maderavida-backup
#   sudo mkdir -p /var/backups/maderavida
#
# Programar diario a las 03:00 (crontab -e como root):
#   0 3 * * * /usr/local/bin/maderavida-backup >> /var/log/maderavida/backup.log 2>&1

set -euo pipefail

ENV_FILE="/srv/maderavida/.env"
BACKUP_DIR="/var/backups/maderavida"
RETENTION_DAYS=30
MEDIA_DIR="/srv/maderavida/media"

# Carga DB_NAME, DB_USER, DB_PASSWORD desde el .env del proyecto
if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: no se encontro $ENV_FILE" >&2
    exit 1
fi
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

mkdir -p "$BACKUP_DIR"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
SQL_FILE="$BACKUP_DIR/madera_vida_${TIMESTAMP}.sql.gz"

echo "[$(date '+%F %T')] Iniciando respaldo de la base de datos..."

# --single-transaction evita bloquear las tablas durante el respaldo.
mysqldump \
    --user="${DB_USER}" \
    --password="${DB_PASSWORD}" \
    --host="${DB_HOST:-127.0.0.1}" \
    --port="${DB_PORT:-3306}" \
    --single-transaction \
    --routines \
    --default-character-set=utf8mb4 \
    "${DB_NAME}" | gzip > "$SQL_FILE"

echo "[$(date '+%F %T')] Base de datos respaldada: $SQL_FILE"

# Respaldo de imagenes subidas (productos, foto de la empresa)
if [[ -d "$MEDIA_DIR" ]]; then
    MEDIA_FILE="$BACKUP_DIR/media_${TIMESTAMP}.tar.gz"
    tar -czf "$MEDIA_FILE" -C "$(dirname "$MEDIA_DIR")" "$(basename "$MEDIA_DIR")"
    echo "[$(date '+%F %T')] Media respaldada: $MEDIA_FILE"
fi

# Verificacion: el dump no debe estar vacio ni corrupto
if ! gzip -t "$SQL_FILE" 2>/dev/null; then
    echo "ERROR: el respaldo esta corrupto: $SQL_FILE" >&2
    exit 1
fi

# Rotacion: elimina respaldos mas antiguos que RETENTION_DAYS
find "$BACKUP_DIR" -name '*.gz' -type f -mtime "+${RETENTION_DAYS}" -delete
echo "[$(date '+%F %T')] Respaldo completado. Retencion: ${RETENTION_DAYS} dias."
