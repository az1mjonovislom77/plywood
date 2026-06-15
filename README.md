# Plywood Inventory Management System

Backend API for managing plywood sales operations — products, orders, customers, suppliers, employees, and financial reporting.

## Overview

This system handles the full lifecycle of a plywood business:
- Warehouse acceptance of goods (with USD/UZS multi-currency support)
- Sales orders with cutting and banding services
- Customer debt tracking and overpayment management
- Supplier debt and payment management
- Employee salary payments
- Expense approval workflow
- Financial dashboard and analytics

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 5.2 + Django REST Framework |
| Auth | JWT (djangorestframework-simplejwt) |
| Database | PostgreSQL (production), SQLite (development) |
| Cache / Queue | Redis + Celery |
| Export | openpyxl, python-docx, reportlab |
| Image processing | Pillow |
| Admin UI | django-jazzmin |

## Role System

The system has 4 roles with separate permissions:

| Role | Access |
|---|---|
| `manager` | Full access |
| `seller` | Orders, basket, customers |
| `cashier` | Order acceptance, payments |
| `warehouseman` | Product acceptance, warehouse |

## Key Features

- **Multi-currency**: Arrival prices stored in both USD and UZS using daily exchange rates
- **FIFO pricing**: Product prices update on each accepted acceptance
- **Order workflow**: Seller creates → Cashier accepts/cancels
- **Expense workflow**: Small expenses auto-approved, large ones (≥1,000,000) require manager approval
- **Acceptance workflow**: Create → Accept (updates stock and supplier debt) or Cancel
- **Rate limiting**: 50 req/min (anonymous), 400 req/min (authenticated)
- **Health check**: `GET /health/` — checks DB and cache connectivity

## Project Structure

```
config/          - Django settings (base / local / production)
user/            - Custom user model with roles
product/         - Products, categories, image validation
category/        - Product categories
acceptance/      - Goods acceptance from suppliers
order/           - Sales orders, basket, cutting, banding
customer/        - Customer management and debt tracking
supplier/        - Supplier management and payments
employee/        - Employee salary payments
utils/           - Expenses, notifications, shared services
```

## Setup

### Requirements

- Python 3.11+
- PostgreSQL
- Redis

### Installation

```bash
git clone https://github.com/az1mjonovislom77/plywood.git
cd plywood
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/plywood
REDIS_URL=redis://localhost:6379/0
```

### Run

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API documentation: `http://127.0.0.1:8000/api/schema/swagger-ui/`

Health check: `http://127.0.0.1:8000/health/`

### Run tests

```bash
python manage.py test
```

### Run Celery worker (for background tasks)

```bash
celery -A config worker -l info
```
