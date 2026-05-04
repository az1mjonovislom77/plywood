# Plywood Project

## Description
The Plywood Project is a comprehensive web application built using Django and Django REST Framework, designed for e-commerce or inventory management. It provides a robust backend for managing users, products, categories, orders, customers, and suppliers. The system is equipped with a powerful API, asynchronous task processing, and potential integration with external services like a Telegram bot for enhanced functionality and user interaction.

## Features
*   **User Management**: Secure user authentication and authorization using JWT (JSON Web Tokens).
*   **Product Catalog**: Comprehensive management of products, categories, and suppliers.
*   **Order Processing**: Efficient handling of customer orders.
*   **RESTful API**: A well-documented API for all core functionalities, built with Django REST Framework.
*   **Asynchronous Tasks**: Background task processing using Celery and Redis for improved performance (e.g., sending notifications, report generation).
*   **Telegram Bot Integration**: Potential integration with a Telegram bot for real-time updates, order notifications, or customer support.
*   **Custom Admin Interface**: Enhanced and user-friendly Django administration panel powered by Django Jazzmin.
*   **Multi-language Support**: Internationalization capabilities for a broader audience.
*   **API Documentation**: Interactive API documentation (Swagger/OpenAPI) generated using `drf-spectacular` and `drf-yasg`.
*   **Reporting & Data Export**: Functionality to generate and export data in various formats (e.g., Excel, Word, PDF).
*   **Image Processing**: Handling and optimization of product images.

## Technologies Used
*   Python
*   Django
*   Django REST Framework
*   Celery
*   Redis
*   PostgreSQL (via `psycopg2-binary`)
*   `django-filter`
*   `aiofiles`, `aiogram`, `aiohttp` (for async operations, potentially Telegram bot)
*   `django-cors-headers`
*   `django-jazzmin`
*   `django-modeltranslation`
*   `django-redis`
*   `djangorestframework_simplejwt`
*   `drf-spectacular`, `drf-yasg` (for API documentation)
*   `gunicorn` (for production deployment)
*   `openpyxl`, `python-docx`, `reportlab`, `lxml` (for document generation)
*   `pillow`, `pillow_heif` (for image processing)
*   `python-decouple` (for environment variable management)
*   `requests`
*   `django-debug-toolbar` (for development)
*   `escpos` (potentially for receipt printing)

## Setup and Installation

### Prerequisites
*   Python 3.x
*   pip
*   PostgreSQL database server

### Steps
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/az1mjonovislom77/plywood.git
    cd plywood
    ```
2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables**:
    Create a `.env` file in the project root based on a `.env.example` (if available) or set environment variables for database connection, secret key, etc.
    Example `.env` content:
    ```
    SECRET_KEY='your_django_secret_key'
    DEBUG=True
    DATABASE_URL='postgres://user:password@host:port/database_name'
    REDIS_URL='redis://localhost:6379/0'
    TELEGRAM_BOT_TOKEN='your_telegram_bot_token'
    ```
5.  **Apply database migrations**:
    ```bash
    python manage.py migrate
    ```
6.  **Create a superuser** (optional, for admin access):
    ```bash
    python manage.py createsuperuser
    ```
7.  **Run the development server**:
    ```bash
    python manage.py runserver
    ```
    The application will be accessible at `http://127.0.0.1:8000/`.
    The Django Admin panel will be at `http://127.0.0.1:8000/admin/`.
    API documentation (Swagger UI) will be available at `http://127.0.0.1:8000/swagger/` or `http://127.0.0.1:8000/redoc/`.

## Usage

### Web Interface
Access the main application and Django Admin panel through your web browser after running the development server.

### API Endpoints
The project exposes a comprehensive set of RESTful API endpoints. You can explore them via the interactive API documentation:
*   **Swagger UI**: `http://127.0.0.1:8000/swagger/`
*   **ReDoc**: `http://127.0.0.1:8000/redoc/`

Common API patterns include:
*   `/api/users/`
*   `/api/products/`
*   `/api/categories/`
*   `/api/orders/`
*   `/api/customers/`
*   `/api/suppliers/`

Authentication is typically handled via JWT tokens obtained from an authentication endpoint (e.g., `/api/token/`).

### Telegram Bot (if configured)
If the Telegram bot integration is active, users can interact with the system through the bot for specific functionalities (e.g., checking order status, receiving notifications).

## Contributing
We welcome contributions to the Plywood Project! If you'd like to contribute, please follow these steps:
1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and ensure they adhere to the project's coding standards.
4.  Write appropriate tests for your changes.
5.  Submit a pull request with a clear description of your changes.
