from rest_framework.permissions import BasePermission
from user.models import User


class IsCashier(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.UserRoles.CASHIER


class IsSeller(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.UserRoles.SELLER


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.UserRoles.MANAGER


class IsWarehouseman(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.UserRoles.WAREHOUSEMAN


class IsCashierOrManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            User.UserRoles.CASHIER,
            User.UserRoles.MANAGER,
        )


class IsSellerOrManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            User.UserRoles.SELLER,
            User.UserRoles.MANAGER,
        )
