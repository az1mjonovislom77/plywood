from django.db import transaction
from django.db.models import F
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from acceptance.models import Acceptance, AcceptanceHistory, CurrencyRate
from product.models import Product
from supplier.models import Supplier, SupplierTransaction


class AcceptanceWorkflowService:
    @staticmethod
    @transaction.atomic
    def create(data, user):
        rate_value = None
        price_type = data.get("price_type")
        arrival_price = data.get("arrival_price", 0)
        sale_price = data.get("sale_price", 0)
        arrival_date = data.get("arrival_date", timezone.localdate())

        arrival_price_in_dollar = 0
        sale_price_in_dollar = 0
        arrival_price_in_sum = 0
        sale_price_in_sum = 0

        if price_type == Acceptance.PriceType.DOLLAR:
            arrival_price_in_dollar = arrival_price
            sale_price_in_dollar = sale_price
            rate = CurrencyRate.objects.filter(date__lte=arrival_date).order_by("-date").first()
            if not rate:
                raise ValueError("Dollar rate not found")
            rate_value = rate.rate
            arrival_price_in_sum = arrival_price * rate_value
            sale_price_in_sum = sale_price * rate_value
        else:
            arrival_price_in_sum = arrival_price
            sale_price_in_sum = sale_price
            rate = CurrencyRate.objects.filter(date__lte=arrival_date).order_by("-date").first()
            if rate and rate.rate > 0:
                arrival_price_in_dollar = arrival_price / rate.rate
                sale_price_in_dollar = sale_price / rate.rate
                rate_value = rate.rate

        data["arrival_price_in_dollar"] = arrival_price_in_dollar
        data["sale_price_in_dollar"] = sale_price_in_dollar
        data["arrival_price_in_sum"] = arrival_price_in_sum
        data["sale_price_in_sum"] = sale_price_in_sum

        acceptance = Acceptance.objects.create(**data)

        AcceptanceHistory.objects.create(
            acceptance=acceptance,
            user=user,
            action=AcceptanceHistory.Action.CREATE,
            supplier=acceptance.supplier,
            product=acceptance.product,
            arrival_price=acceptance.arrival_price,
            sale_price=acceptance.sale_price,
            exchange_rate=rate_value,
            price_type=acceptance.price_type,
            count=acceptance.count,
            arrival_date=acceptance.arrival_date,
            description=acceptance.description,
        )
        return acceptance

    @staticmethod
    @transaction.atomic
    def accept(acceptance_id, user):
        acceptance = Acceptance.objects.select_for_update().get(id=acceptance_id)
        if acceptance.acceptance_status != Acceptance.AcceptanceStatus.WAITING:
            raise ValueError("Acceptance already processed")

        Product.objects.filter(pk=acceptance.product_id).update(
            count=F("count") + acceptance.count,
            arrival_price=acceptance.arrival_price_in_sum,
            arrival_price_in_dollar=acceptance.arrival_price_in_dollar,
            sale_price=acceptance.sale_price_in_sum,
            sale_price_in_dollar=acceptance.sale_price_in_dollar
        )

        total_amount = acceptance.arrival_price_in_sum * acceptance.count

        if acceptance.supplier_id:
            Supplier.objects.filter(pk=acceptance.supplier_id).update(debt=F("debt") + total_amount)

            SupplierTransaction.objects.create(
                supplier_id=acceptance.supplier_id,
                transaction_type=SupplierTransaction.TransactionType.PURCHASE,
                amount=total_amount,
                description=f"Acceptance #{acceptance.id}"
            )

        acceptance.acceptance_status = Acceptance.AcceptanceStatus.ACCEPT
        acceptance.accepted_by = user
        acceptance.accepted_at = timezone.now()

        acceptance.save(update_fields=[
            "acceptance_status",
            "accepted_by",
            "accepted_at"
        ])

        AcceptanceHistory.objects.create(
            acceptance=acceptance,
            user=user,
            action=AcceptanceHistory.Action.ACCEPT,
            supplier=acceptance.supplier,
            product=acceptance.product,
            arrival_price=acceptance.arrival_price,
            sale_price=acceptance.sale_price,
            price_type=acceptance.price_type,
            count=acceptance.count,
            arrival_date=acceptance.arrival_date,
        )

        return acceptance

    @staticmethod
    @transaction.atomic
    def cancel(acceptance_id, user, description=None):
        acceptance = Acceptance.objects.select_for_update().get(id=acceptance_id)

        if acceptance.acceptance_status != Acceptance.AcceptanceStatus.WAITING:
            raise ValueError("Acceptance already processed")

        acceptance.acceptance_status = Acceptance.AcceptanceStatus.CANCEL
        acceptance.save(update_fields=["acceptance_status"])
        AcceptanceHistory.objects.create(
            acceptance=acceptance,
            user=user,
            action=AcceptanceHistory.Action.CANCEL,
            supplier=acceptance.supplier,
            product=acceptance.product,
            arrival_price=acceptance.arrival_price,
            sale_price=acceptance.sale_price,
            price_type=acceptance.price_type,
            count=acceptance.count,
            arrival_date=acceptance.arrival_date,
            description=description
        )

        return acceptance