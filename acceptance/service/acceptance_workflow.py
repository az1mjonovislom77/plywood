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

        acceptance = Acceptance.objects.create(**data)

        rate_value = None

        if acceptance.price_type == Acceptance.PriceType.DOLLAR:
            rate = CurrencyRate.objects.filter(
                date__lte=acceptance.arrival_date
            ).order_by("-date").first()

            if not rate:
                raise ValueError("Dollar rate not found")

            rate_value = rate.rate

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

        arrival_price = acceptance.arrival_price
        sale_price = acceptance.sale_price

        if acceptance.price_type == Acceptance.PriceType.DOLLAR:

            rate = CurrencyRate.objects.filter(
                date__lte=acceptance.arrival_date
            ).order_by("-date").first()

            if not rate:
                raise ValueError("Dollar rate not found")

            arrival_price = (arrival_price * rate.rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            sale_price = (sale_price * rate.rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        Product.objects.filter(pk=acceptance.product_id).update(
            count=F("count") + acceptance.count,
            arrival_price=arrival_price,
            sale_price=sale_price
        )

        total_amount = arrival_price * acceptance.count

        if acceptance.supplier_id:
            Supplier.objects.filter(pk=acceptance.supplier_id).update(
                debt=F("debt") + total_amount
            )

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