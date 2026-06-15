import logging
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return response

    if isinstance(exc, ValueError):
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, ObjectDoesNotExist):
        return Response({"detail": "Topilmadi"}, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, DjangoValidationError):
        return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)

    view = context.get("view")
    logger.error(
        "Unhandled exception in %s: %s",
        view.__class__.__name__ if view else "unknown",
        str(exc),
        exc_info=True,
    )
    return None
