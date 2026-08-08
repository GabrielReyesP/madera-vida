# 🪵 Madera & Vida

**ERP ligero + e-commerce** para una microempresa chilena de productos de madera.
Integra tienda online, gestión de inventario, control de pedidos y un módulo de
Recursos Humanos con liquidaciones de sueldo conformes a la legislación laboral chilena.

Construido con Django 5.2, MySQL y HTMX, con control de acceso por roles y
cumplimiento de normativa tributaria (IVA 19%), laboral (Código del Trabajo) y
de protección de datos (Ley 19.628 / 21.719).

---

## ✨ Funcionalidades

### Sitio público y tienda
- Catálogo por categorías con búsqueda, filtros e imágenes.
- Precios mostrados con IVA incluido; boleta que desglosa neto + IVA.
- Carrito en sesión con validación de stock en tiempo real.
- Checkout **como invitado o cliente registrado**, con validación de RUT.
- Pago simulado, número de pedido correlativo y correo de confirmación.
- Historial de pedidos para clientes registrados.

### Panel interno (por roles)
- **Jefatura / Administración**: acceso completo — productos, precios, stock,
  pedidos, horas extras, trabajadores, auditoría.
- **RRHH**: trabajadores, liquidaciones, anticipos/bonos/descuentos.
- **Venta**: gestión de pedidos y su ciclo de estados.
- Dashboard con gráfico de ventas (Chart.js), alertas de stock bajo y horas extras del mes.
- Log de auditoría con usuario, acción, cambio antes/después e IP.

### Recursos Humanos
- Alta de trabajadores con contraseña asignada por administración.
- Validación de RUT (módulo 11) y de sueldo mínimo vigente **configurable**.
- Horas extras con recargo del 50% calculado automáticamente (Art. 32).
- Liquidaciones mensuales: imponible, AFP, salud 7%, anticipos, descuentos y líquido.
- AFPs y sueldo mínimo administrables sin tocar código.

### Reportes
- Exportación a Excel (openpyxl) de ventas, liquidaciones y horas extras.
- Filtros por período, con totales calculados mediante fórmulas reales de Excel.

### Privacidad (Ley 19.628 / 21.719)
- Centro de privacidad con derechos de **acceso** (descarga de datos en JSON),
  **rectificación** y **supresión**.
- La eliminación anonimiza los pedidos en lugar de borrarlos, para respetar las
  obligaciones de conservación contable.

---

## 🛠️ Stack técnico

| Capa | Tecnología |
|---|---|
| Backend | Django 5.2 (Python 3.12+) |
| Base de datos | MySQL 8.x (`utf8mb4`) |
| Frontend | Django Templates + HTMX + Tailwind CSS + Chart.js |
| Reportes | openpyxl |
| Imágenes | Pillow |
| Configuración | python-dotenv, settings separados por entorno |
| Producción | Gunicorn + Nginx + Let's Encrypt |

---

## 📁 Arquitectura

```
madera_vida/
├── apps/
│   ├── core/        # CompanyInfo, AuditLog, configs (sueldo mínimo, AFP)
│   ├── accounts/    # CustomUser (login por email), perfiles, roles, privacidad
│   ├── catalog/     # Categorías y productos (SKU e IVA automáticos)
│   ├── store/       # Carrito, pedidos, checkout, boleta
│   ├── hr/          # Horas extras, liquidaciones, ajustes
│   └── dashboard/   # Panel interno, métricas y reportes Excel
├── config/
│   └── settings/    # base.py · development.py · production.py
├── templates/
├── deploy/          # Gunicorn, Nginx, respaldos y guía de despliegue
└── requirements.txt
```

**Decisiones de diseño destacadas:**
- El **precio neto** es la fuente de verdad; el precio con IVA se deriva de una tasa
  configurable, evitando el 19% incrustado en el código.
- Las líneas de pedido guardan una *foto* del producto y su precio al momento de la
  compra, de modo que las boletas históricas no cambian si después sube un precio.
- El stock se descuenta al confirmar el pedido, dentro de una transacción con
  `select_for_update()`, evitando la sobreventa ante checkouts simultáneos.
- Los valores legales (sueldo mínimo, % de AFP, jornada semanal) viven en base de
  datos o variables de entorno, no en el código: la ley cambia, el sistema no.

---

## 🚀 Instalación local

```bash
git clone https://github.com/GabrielReyesP/madera-vida.git
cd madera-vida

python -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crea la base de datos:
```sql
CREATE DATABASE madera_vida CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Copia `.env.example` a `.env` y completa tus credenciales. Luego:

```bash
python manage.py migrate
python manage.py seed_hr_config     # AFPs y sueldo mínimo iniciales
python manage.py createsuperuser
python manage.py runserver
```

- Tienda: `http://127.0.0.1:8000/`
- Panel interno: `http://127.0.0.1:8000/dashboard/` (requiere perfil de trabajador)
- Admin de Django: `http://127.0.0.1:8000/admin/`

---

## 🧪 Tests

```bash
python manage.py test
```

Cubren las reglas de negocio críticas:
- Validación de RUT (módulo 11), incluyendo dígito verificador `K`.
- Validación de sueldo mínimo contra la configuración vigente.
- Matriz de permisos de los cuatro roles.
- Cálculo y desglose de IVA; redondeo a peso chileno.
- Generación de SKU sin colisiones entre categorías similares.
- Carrito: límites de stock al agregar y actualizar.
- Checkout: descuento de stock, totales e inmutabilidad del precio histórico.
- Fórmulas previsionales: hora extra 1.5x, AFP, salud 7% y líquido a pagar.

---

## 🚢 Despliegue

Guía completa en [`deploy/README.md`](deploy/README.md): Gunicorn con systemd,
Nginx como proxy inverso, HTTPS con Let's Encrypt y respaldos automáticos de
base de datos con rotación.

---

## 📌 Fuera del alcance actual

Facturación electrónica SII (DTE), pasarela de pago real (Webpay/Transbank),
envíos a domicilio y aplicación móvil nativa.

---

## 👤 Autor

**Gabriel Alonso Reyes Pino** — proyecto de portafolio de desarrollo full-stack,
construido sobre un caso de uso real de microempresa chilena.

## 📄 Licencia

Uso educativo y de portafolio personal.
