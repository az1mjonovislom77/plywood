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
        low_stock_products = Product.objects.filter(count__lt=threshold).values("id", "name", "count").order_by("count")
        total_product_types = Product.objects.count()

        return {
            "product_types": total_product_types,
            "low_stock": list(low_stock_products)
        }
