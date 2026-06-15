from product.models import Product


class ProductSelector:
    @staticmethod
    def active_products():
        return Product.objects.select_related("category").filter(is_active=True)

    @staticmethod
    def inactive_products():
        return Product.objects.select_related("category").filter(is_active=False)

    @staticmethod
    def products_by_category(category_id):
        return Product.objects.select_related("category").filter(category_id=category_id, is_active=True)

    @staticmethod
    def product_by_id(product_id):
        return Product.objects.select_related("category").filter(id=product_id, is_active=True).first()
