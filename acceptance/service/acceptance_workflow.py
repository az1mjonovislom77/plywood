from django.db import transaction
from django.db.models import F
from django.utils import timezone
from decimal import Decimal
from acceptance.models import Acceptance, AcceptanceHistory, CurrencyRate
from product.models import Product
from supplier.models import Supplier, SupplierTransaction
from supplier.service.supplier import SupplierService


class AcceptanceWorkflowService:
    @staticmethod
    @transaction.atomic
    def create(data, user):
        arrival_price_input = data.get("arrival_price", 0)
        sale_price_input = data.get("sale_price", 0)
        arrival_date = data.get("arrival_date", timezone.localdate())

        rate = CurrencyRate.objects.filter(date__lte=arrival_date).order_by("-date").first()

        if not rate:
            raise ValueError(f"Currency rate for {arrival_date} or earlier not found.")

        rate_value = rate.rate

        data["arrival_price_in_dollar"] = arrival_price_input
        data["sale_price_in_dollar"] = sale_price_input
        data["arrival_price_in_sum"] = (Decimal(arrival_price_input) * rate_value).quantize(Decimal("0.01"))
        data["sale_price_in_sum"] = (Decimal(sale_price_input) * rate_value).quantize(Decimal("0.01"))
        data["price_type"] = Acceptance.PriceType.DOLLAR

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
    def update(acceptance, data, user):
        old_count = Decimal(acceptance.count)
        old_debt = Decimal(acceptance.arrival_price_in_sum) * old_count
        is_accepted = str(acceptance.acceptance_status) == "accept"

        new_arrival_price = Decimal(data.get("arrival_price", acceptance.arrival_price))
        new_sale_price = Decimal(data.get("sale_price", acceptance.sale_price))
        new_count = Decimal(data.get("count", acceptance.count))
        arrival_date = data.get("arrival_date", acceptance.arrival_date)
        rate = CurrencyRate.objects.filter(date__lte=arrival_date).order_by("-date").first()

        if not rate:
            raise ValueError(f"Currency rate for {arrival_date} or earlier not found.")

        rate_value = rate.rate
        new_arrival_price_in_sum = (new_arrival_price * rate_value).quantize(Decimal("0.01"))
        new_sale_price_in_sum = (new_sale_price * rate_value).quantize(Decimal("0.01"))

        if is_accepted:
            count_difference = new_count - old_count
            new_debt = new_arrival_price_in_sum * new_count
            Product.objects.filter(pk=acceptance.product_id).update(
                count=F("count") + count_difference,
                arrival_price=new_arrival_price,
                sale_price=new_sale_price,
                arrival_price_in_sum=new_arrival_price_in_sum,
                sale_price_in_sum=new_sale_price_in_sum
            )

            old_supplier = acceptance.supplier
            new_supplier = data.get("supplier", old_supplier)
            suppliers_to_update = set()
            if old_supplier:
                suppliers_to_update.add(old_supplier.id)
            if new_supplier:
                suppliers_to_update.add(new_supplier.id)

            locked_suppliers = {}
            if suppliers_to_update:
                locked_suppliers = {
                    s.id: s for s in Supplier.objects.select_for_update().filter(id__in=suppliers_to_update)
                }

            if old_supplier and old_supplier.id in locked_suppliers:
                old_supplier = locked_suppliers[old_supplier.id]

            if new_supplier and new_supplier.id in locked_suppliers:
                new_supplier = locked_suppliers[new_supplier.id]

            purchase_txn = SupplierTransaction.objects.filter(
                transaction_type=SupplierTransaction.TransactionType.PURCHASE,
                description=f"Acceptance #{acceptance.id}").first()

            if new_supplier:
                if purchase_txn:
                    purchase_txn.amount = new_debt
                    purchase_txn.supplier = new_supplier
                    purchase_txn.save(update_fields=["amount", "supplier"])
                else:
                    SupplierTransaction.objects.create(
                        supplier=new_supplier,
                        transaction_type=SupplierTransaction.TransactionType.PURCHASE,
                        amount=new_debt,
                        description=f"Acceptance #{acceptance.id}"
                    )
                SupplierService.recalculate_debt(new_supplier)
            else:
                if purchase_txn:
                    purchase_txn.delete()

            if old_supplier and old_supplier != new_supplier:
                SupplierService.recalculate_debt(old_supplier)

        acceptance.arrival_price = new_arrival_price
        acceptance.sale_price = new_sale_price
        acceptance.count = new_count
        acceptance.arrival_date = arrival_date
        acceptance.arrival_price_in_dollar = new_arrival_price
        acceptance.sale_price_in_dollar = new_sale_price
        acceptance.arrival_price_in_sum = new_arrival_price_in_sum
        acceptance.sale_price_in_sum = new_sale_price_in_sum
        acceptance.price_type = Acceptance.PriceType.DOLLAR

        for key, value in data.items():
            if key not in [
                "arrival_price",
                "sale_price",
                "count",
                "arrival_date",
                "supplier"
            ]:
                setattr(acceptance, key, value)

        if "supplier" in data:
            acceptance.supplier = data["supplier"]

        acceptance.save()

        AcceptanceHistory.objects.create(
            acceptance=acceptance,
            user=user,
            action=AcceptanceHistory.Action.UPDATE,
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

        acceptance.refresh_from_db()
        if acceptance.supplier:
            acceptance.supplier.refresh_from_db()

        return acceptance

    @staticmethod
    @transaction.atomic
    def accept(acceptance_id, user):
        acceptance = Acceptance.objects.select_for_update().get(id=acceptance_id)

        if acceptance.acceptance_status != Acceptance.AcceptanceStatus.WAITING:
            raise ValueError("Acceptance already processed")

        Product.objects.filter(pk=acceptance.product_id).update(
            count=F("count") + acceptance.count,
            arrival_price=acceptance.arrival_price_in_dollar,
            sale_price=acceptance.sale_price_in_dollar,
            arrival_price_in_sum=acceptance.arrival_price_in_sum,
            sale_price_in_sum=acceptance.sale_price_in_sum
        )

        total_amount = acceptance.arrival_price_in_sum * acceptance.count

        if acceptance.supplier_id:
            SupplierTransaction.objects.create(
                supplier_id=acceptance.supplier_id,
                transaction_type=SupplierTransaction.TransactionType.PURCHASE,
                amount=total_amount,
                description=f"Acceptance #{acceptance.id}"
            )

            supplier = Supplier.objects.select_for_update().get(pk=acceptance.supplier_id)
            SupplierService.recalculate_debt(supplier)

        acceptance.acceptance_status = Acceptance.AcceptanceStatus.ACCEPT
        acceptance.accepted_by = user
        acceptance.accepted_at = timezone.now()
        acceptance.save(update_fields=["acceptance_status", "accepted_by", "accepted_at"])
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
