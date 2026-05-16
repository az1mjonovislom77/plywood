import re
from decimal import Decimal
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from customer.models import Customer
from customer.service.cover_debt import DebtService
from order.models import Order, OrderItem
from product.models import Product
from user.models import User


class Command(BaseCommand):
    help = "Exceldan debt va covered payment import qiladi"

    @transaction.atomic
    def handle(self, *args, **kwargs):

        file_path = "debt.xlsx"

        user = User.objects.first()

        if not user:
            self.stdout.write(
                self.style.ERROR("User topilmadi")
            )
            return

        product, _ = Product.objects.get_or_create(
            name="TEST_DEBT_PRODUCT",
            defaults={
                "sale_price": Decimal("1.00"),
                "arrival_price": Decimal("1.00"),
                "count": Decimal("940145322.270"),
            }
        )

        product.sale_price = Decimal("1.00")
        product.count = Decimal("940145322.270")
        product.save()

        df = pd.read_excel(file_path, header=None)

        created_orders = 0
        covered_payments = 0

        for index, row in df.iterrows():

            try:

                customer_name = str(row[0]).strip().lower()
                customer_name = re.sub(r"\s+", " ", customer_name)
                customer_name = customer_name.replace(".", "")
                customer_name = customer_name.replace(",", "")

                if not customer_name or customer_name == "nan":
                    continue

                customers = Customer.objects.all()

                customer = None

                for c in customers:

                    db_name = c.full_name.strip().lower()

                    db_name = re.sub(r"\s+", " ", db_name)

                    db_name = db_name.replace(".", "")
                    db_name = db_name.replace(",", "")

                    if db_name == customer_name:
                        customer = c
                        break
                if not customer:
                    customer = Customer.objects.filter(
                        full_name__istartswith=customer_name
                    ).first()

                if not customer:
                    self.stdout.write(
                        self.style.WARNING(
                            f"CUSTOMER TOPILMADI row={index + 1} name={customer_name}"
                        )
                    )
                    continue

                debt = Decimal("0")

                debt_value = row[1]

                if not pd.isna(debt_value):

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

                        if cleaned not in ["", "-", ".", "-."]:
                            debt = abs(Decimal(cleaned))

                    except Exception:
                        self.stdout.write(
                            self.style.WARNING(
                                f"INVALID DEBT row {index + 1}: {debt_value}"
                            )
                        )

                covered_amount = Decimal("0")

                if len(row) > 2 and not pd.isna(row[2]):

                    try:

                        covered_str = (
                            str(row[2])
                            .strip()
                            .replace(" ", "")
                            .replace(",", ".")
                        )

                        cleaned_covered = ""

                        for char in covered_str:
                            if char.isdigit() or char in [".", "-"]:
                                cleaned_covered += char

                        if cleaned_covered not in ["", "-", ".", "-."]:
                            covered_amount = abs(
                                Decimal(cleaned_covered)
                            )

                    except Exception:
                        self.stdout.write(
                            self.style.WARNING(
                                f"INVALID COVERED row {index + 1}: {row[2]}"
                            )
                        )

                if debt <= 0 and covered_amount <= 0:
                    continue

                if debt > 0:

                    quantity = Decimal(str(debt)).quantize(
                        Decimal("0.001")
                    )

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

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=Decimal("1.00"),
                        original_sell_price=Decimal("1.00"),
                        new_sell_price=Decimal("1.00"),
                        exchange_rate=Decimal("1.00"),
                        price_in_dollar=Decimal("1.00"),
                        new_price_in_dollar=Decimal("1.00"),
                    )

                    order.calculate_total()

                    order.total_price = Decimal(
                        str(order.total_price).replace(",", ".")
                    )

                    order.save()

                    created_orders += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{customer.full_name} -> "
                            f"{debt} so'm debt order yaratildi"
                        )
                    )

                if covered_amount > 0:

                    DebtService.cover_debt(
                        customer_id=customer.id,
                        amount=covered_amount
                    )

                    covered_payments += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{customer.full_name} -> "
                            f"{covered_amount} so'm covered payment"
                        )
                    )

            except Exception as e:

                self.stdout.write(
                    self.style.ERROR(
                        f"ERROR row={index + 1} "
                        f"customer={customer_name} "
                        f"error={str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"FINISHED | "
                f"Orders: {created_orders} | "
                f"Covered payments: {covered_payments}"
            )
        )
