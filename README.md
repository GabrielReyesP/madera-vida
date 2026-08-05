# 🪵 Madera & Vida

Sistema web full-stack para una pyme de productos de madera en Chile, que integra **e-commerce** y **gestión de RR.HH.** en una sola plataforma.

Construido con Django, MySQL y HTMX, con foco en buenas prácticas de arquitectura, separación de responsabilidades y datos localizados para el contexto chileno (RUT, sueldo mínimo, IVA, horas extra según el Código del Trabajo).

## ✨ Características

- **Autenticación con roles personalizados** (`admin`, `trabajador`, `cliente`) mediante un modelo `CustomUser` que extiende `AbstractUser`.
- **Catálogo de productos** por categorías.
- **Tienda online**: carrito de compras, órdenes y checkout.
- **Módulo de RR.HH.**: horas extra, liquidaciones de sueldo, ajustes — con constantes chilenas configurables (IVA, sueldo mínimo, jornada semanal, recargo por hora extra).
- **Dashboard** con métricas y gráficos del negocio.
- Interfaz dinámica con **HTMX**, sin necesidad de un framework de frontend pesado.
- Configuración por entornos (`development` / `production`) separada mediante variables de entorno.

## 🛠️ Stack técnico

| Categoría | Tecnología |
|---|---|
| Backend | Django 5.2 |
| Base de datos | MySQL 8.0 (charset `utf8mb4`) |
| Frontend dinámico | HTMX + django-widget-tweaks |
| Gestión de imágenes | Pillow |
| Configuración | python-dotenv (variables de entorno) |

## 📁 Estructura del proyecto

```
madera_vida/
├── apps/
│   ├── core/          # Modelos base, configuración global
│   ├── accounts/      # CustomUser, WorkerProfile, CustomerProfile
│   ├── catalog/       # Categorías y productos
│   ├── store/         # Carrito, órdenes, checkout
│   ├── hr/            # Horas extra, liquidaciones, ajustes
│   └── dashboard/     # Métricas y visualización
├── config/
│   └── settings/      # base.py / development.py / production.py
├── templates/
├── static/
└── requirements.txt
```

## 🚀 Instalación local

1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/madera_vida.git
   cd madera_vida
   ```

2. Crea y activa un entorno virtual:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\Activate.ps1
   # macOS / Linux
   source venv/bin/activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Crea un archivo `.env` en la raíz del proyecto (usa `.env.example` como referencia):
   ```
   DJANGO_SECRET_KEY=tu_clave_secreta
   DB_NAME=madera_vida
   DB_USER=root
   DB_PASSWORD=tu_password
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```

5. Crea la base de datos en MySQL:
   ```sql
   CREATE DATABASE madera_vida
       CHARACTER SET utf8mb4
       COLLATE utf8mb4_unicode_ci;
   ```

6. Aplica las migraciones y crea un superusuario:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

7. Levanta el servidor:
   ```bash
   python manage.py runserver
   ```

   Visita `http://127.0.0.1:8000/admin/` para acceder al panel de administración.

## 🗺️ Roadmap

- [x] Configuración base del proyecto y entornos
- [x] Modelo de usuario personalizado con roles
- [ ] Modelos de catálogo (`Category`, `Product`)
- [ ] Carrito de compras y checkout
- [ ] Módulo de horas extra y liquidaciones
- [ ] Dashboard con métricas

## 👤 Autor

Desarrollado por [tu nombre] como parte de portafolio de desarrollo full-stack.

## 📄 Licencia

Este proyecto es de uso educativo / portafolio personal.
