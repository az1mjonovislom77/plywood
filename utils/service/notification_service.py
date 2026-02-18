from product.models import Product
from utils.models import NotificationSettings


class ProductNotificationService:

    @staticmethod
    def get_low_stock_threshold():
        settings = NotificationSettings.objects.only("low_stock_threshold").first()
        return settings.low_stock_threshold if settings else 20

    @staticmethod
    def get_low_stock_info():
        threshold = ProductNotificationService.get_low_stock_threshold()
        queryset = Product.objects.filter(count__lt=threshold).values("id", "name", "count").order_by("count")

        return {
            "low_stock_products": queryset.count(),
            "products": list(queryset)
        }
