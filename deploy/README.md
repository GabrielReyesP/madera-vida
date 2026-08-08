# Guía de despliegue — Madera & Vida

Despliegue en VM Ubuntu con **Gunicorn + Nginx + MySQL + HTTPS**.

## 1. Preparar el servidor

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip mysql-server nginx git \
                    pkg-config python3-dev default-libmysqlclient-dev build-essential

# Usuario dedicado (sin shell de login, por seguridad)
sudo adduser --system --group --home /srv/maderavida maderavida
sudo mkdir -p /var/log/maderavida
sudo chown maderavida:www-data /var/log/maderavida
```

## 2. Base de datos

```bash
sudo mysql -u root -p
```
```sql
CREATE DATABASE madera_vida CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'maderavida'@'localhost' IDENTIFIED BY 'una-contraseña-fuerte';
GRANT ALL PRIVILEGES ON madera_vida.* TO 'maderavida'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 3. Código y entorno virtual

```bash
sudo -u maderavida git clone <tu-repo> /srv/maderavida
cd /srv/maderavida
sudo -u maderavida python3 -m venv venv
sudo -u maderavida ./venv/bin/pip install -r requirements.txt
sudo -u maderavida ./venv/bin/pip install gunicorn
```

## 4. Variables de entorno

Crea `/srv/maderavida/.env` (nunca se sube a Git):

```bash
DJANGO_ENV=production
DJANGO_SECRET_KEY=<generar-con-el-comando-de-abajo>
DJANGO_ALLOWED_HOSTS=maderavida.cl,www.maderavida.cl
DJANGO_CSRF_TRUSTED_ORIGINS=https://maderavida.cl,https://www.maderavida.cl

DB_NAME=madera_vida
DB_USER=maderavida
DB_PASSWORD=una-contraseña-fuerte
DB_HOST=127.0.0.1
DB_PORT=3306

EMAIL_HOST=smtp.tu-proveedor.cl
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@maderavida.cl
EMAIL_HOST_PASSWORD=<password-smtp>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Madera & Vida <noreply@maderavida.cl>

IVA_RATE=0.19
MINIMUM_WAGE=539000
WEEKLY_HOURS=44
```

Generar la SECRET_KEY:
```bash
./venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Proteger el archivo:
```bash
sudo chown maderavida:maderavida /srv/maderavida/.env
sudo chmod 600 /srv/maderavida/.env
```

## 5. Migraciones, estáticos y datos iniciales

```bash
cd /srv/maderavida
sudo -u maderavida ./venv/bin/python manage.py migrate
sudo -u maderavida ./venv/bin/python manage.py collectstatic --noinput
sudo -u maderavida ./venv/bin/python manage.py seed_hr_config
sudo -u maderavida ./venv/bin/python manage.py createsuperuser
```

## 6. Gunicorn (systemd)

```bash
sudo cp deploy/gunicorn.service /etc/systemd/system/maderavida.service
sudo systemctl daemon-reload
sudo systemctl enable --now maderavida
sudo systemctl status maderavida
```

## 7. Nginx + HTTPS

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/maderavida
sudo ln -s /etc/nginx/sites-available/maderavida /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Certificado TLS gratuito (Let's Encrypt)
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d maderavida.cl -d www.maderavida.cl
```

Certbot renueva automáticamente. Verificar:
```bash
sudo certbot renew --dry-run
```

## 8. Respaldos automáticos

```bash
sudo cp deploy/backup_db.sh /usr/local/bin/maderavida-backup
sudo chmod +x /usr/local/bin/maderavida-backup
sudo mkdir -p /var/backups/maderavida

# Probar manualmente antes de programar
sudo /usr/local/bin/maderavida-backup

# Programar diario a las 03:00
sudo crontab -e
# Agregar:
0 3 * * * /usr/local/bin/maderavida-backup >> /var/log/maderavida/backup.log 2>&1
```

**Restaurar un respaldo:**
```bash
gunzip < /var/backups/maderavida/madera_vida_YYYYMMDD_HHMMSS.sql.gz | \
    mysql -u maderavida -p madera_vida
```

> Recomendación: copiar los respaldos a un destino externo (otro servidor,
> almacenamiento en la nube). Un respaldo que vive en el mismo disco que la
> base de datos no protege ante una falla de hardware.

## 9. Verificación post-despliegue

```bash
# Revisar configuración de seguridad de Django
sudo -u maderavida ./venv/bin/python manage.py check --deploy

# Logs en vivo
sudo journalctl -u maderavida -f
sudo tail -f /var/log/nginx/maderavida.error.log
```

Checklist:
- [ ] El sitio carga por HTTPS y redirige desde HTTP
- [ ] Los archivos estáticos e imágenes de productos se ven correctamente
- [ ] Se puede iniciar sesión y hacer un pedido de prueba
- [ ] Los correos salen (revisa el checkout de prueba)
- [ ] `manage.py check --deploy` no reporta advertencias críticas
- [ ] El respaldo manual generó un `.sql.gz` válido

## 10. Actualizar el sistema en producción

```bash
cd /srv/maderavida
sudo -u maderavida git pull
sudo -u maderavida ./venv/bin/pip install -r requirements.txt
sudo -u maderavida ./venv/bin/python manage.py migrate
sudo -u maderavida ./venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart maderavida
```
