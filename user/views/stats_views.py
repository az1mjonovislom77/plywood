from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from user.services.user_stats import UserStatsService


class UserStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = UserStatsService.dashboard()

        return Response(stats, status=status.HTTP_200_OK)
