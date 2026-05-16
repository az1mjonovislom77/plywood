from decimal import Decimal
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from customer.models import Customer
from order.models import Order, OrderItem
from product.models import Product
from user.models import User


class Command(BaseCommand):
    help = "Exceldan debt order yaratadi"

    @transaction.atomic
    def handle(self, *args, **kwargs):

        file_path = "debt.xlsx"

        user = User.objects.first()

        if not user:
            self.stdout.write(self.style.ERROR("User topilmadi"))
            return

        # TEST PRODUCT
        product, _ = Product.objects.get_or_create(
            name="TEST_DEBT_PRODUCT",
            defaults={
                "sale_price": Decimal("1"),
                "count": Decimal("940145322.270"),
                "arrival_price": Decimal("0"),
            }
        )

        product.sale_price = Decimal("1")
        product.count = Decimal("940145322.270")
        product.save()

        # EXCEL
        df = pd.read_excel(file_path, header=None)

        created_orders = 0

        for index, row in df.iterrows():

            try:
                customer_name = str(row[0]).strip()

                if not customer_name or customer_name == "nan":
                    continue

                debt_value = row[1]

                if pd.isna(debt_value):
                    continue


                try:
                    debt_str = (
                        str(debt_value)
                        .strip()
                        .replace(" ", "")
                        .replace(",", ".")
                    )

                    cleaned = ""

                    for char in debt_str:
                        if char.isdigit() or char in [".", "-"]:
                            cleaned += char

                    if cleaned in ["", "-", ".", "-."]:
                        continue

                    debt = abs(Decimal(cleaned))

                except Exception:
                    self.stdout.write(
                        self.style.WARNING(
                            f"INVALID DEBT row {index + 1}: {debt_value}"
                        )
                    )
                    continue

                if debt <= 0:
                    continue

                customer = Customer.objects.filter(
                    full_name__iexact=customer_name
                ).first()

                if not customer:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Customer topilmadi: {customer_name}"
                        )
                    )
                    continue

                # 1 so'mlik product
                quantity = debt

                # ORDER CREATE
                order = Order.objects.create(
                    user=user,
                    customer=customer,
                    is_anonymous=False,
                    source=Order.OrderSource.SELLER,
                    order_status=Order.OrderStatus.ACCEPT,
                    accepted_by=user,
                    accepted_at=timezone.now(),
                    payment_method=Order.PaymentMethod.NASIYA,
                    covered_amount=Decimal("0"),
                )

                # ORDER ITEM
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=Decimal("1"),
                    original_sell_price=Decimal("1"),
                    new_sell_price=Decimal("1"),
                )

                # TOTAL HISOBLAYDI
                order.calculate_total()
                order.save()

                created_orders += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"{customer.full_name} -> {debt} so'm debt order yaratildi"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"ERROR row {index + 1}: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"FINISHED: {created_orders} ta order yaratildi"
            )
        )