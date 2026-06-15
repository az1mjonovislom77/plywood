import logging
from django.db import connection
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        health = {"status": "ok", "db": "ok", "cache": "ok"}

        try:
            connection.ensure_connection()
        except Exception as e:
            health["db"] = "error"
            health["status"] = "error"
            logger.error("Health check: DB connection failed: %s", str(e))

        try:
            cache.set("health_check", "ok", timeout=5)
            cache.get("health_check")
        except Exception as e:
            health["cache"] = "error"
            health["status"] = "error"
            logger.error("Health check: Cache connection failed: %s", str(e))

        status_code = 200 if health["status"] == "ok" else 503
        return Response(health, status=status_code)
