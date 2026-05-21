from django.db import transaction
from django.db.models import F
from django.utils import timezone
from decimal import Decimal
from acceptance.models import Acceptance, AcceptanceHistory, CurrencyRate
from product.models import Product
from supplier.models import Supplier, SupplierTransaction


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
        old_arrival_price_in_sum = Decimal(acceptance.arrival_price_in_sum)
        old_count = Decimal(acceptance.count)
        is_accepted = str(acceptance.acceptance_status) == "accept"
        
        new_arrival_price = Decimal(data.get("arrival_price", acceptance.arrival_price))
        new_sale_price = Decimal(data.get("sale_price", acceptance.sale_price))
        new_count = Decimal(data.get("count", acceptance.count))
        arrival_date = data.get("arrival_date", acceptance.arrival_date)
        
        rate = CurrencyRate.objects.filter(date__lte=arrival_date).order_by("-date").first()
        if not rate:
            raise ValueError(f"Currency rate for {arrival_date} or earlier not found.")
        rate_value = rate.rate

        acceptance.arrival_price = new_arrival_price
        acceptance.sale_price = new_sale_price
        acceptance.count = new_count
        acceptance.arrival_date = arrival_date
        
        # Update other fields from data avoiding overriding our controlled fields
        for key, value in data.items():
            if key not in ["arrival_price", "sale_price", "count", "arrival_date"]:
                setattr(acceptance, key, value)

        acceptance.arrival_price_in_dollar = new_arrival_price
        acceptance.sale_price_in_dollar = new_sale_price
        acceptance.arrival_price_in_sum = (new_arrival_price * rate_value).quantize(Decimal("0.01"))
        acceptance.sale_price_in_sum = (new_sale_price * rate_value).quantize(Decimal("0.01"))
        acceptance.price_type = Acceptance.PriceType.DOLLAR

        if is_accepted:
            count_difference = new_count - old_count
            
            Product.objects.filter(pk=acceptance.product_id).update(
                count=F("count") + count_difference,
                arrival_price=acceptance.arrival_price_in_dollar,
                sale_price=acceptance.sale_price_in_dollar,
                arrival_price_in_sum=acceptance.arrival_price_in_sum,
                sale_price_in_sum=acceptance.sale_price_in_sum
            )
            
            if acceptance.supplier:
                old_debt = old_arrival_price_in_sum * old_count
                new_debt = acceptance.arrival_price_in_sum * new_count
                debt_difference = new_debt - old_debt

                if debt_difference != Decimal(0):
                    Supplier.objects.filter(pk=acceptance.supplier_id).update(debt=F("debt") + debt_difference)
                    
                    purchase_txn = SupplierTransaction.objects.filter(
                        supplier_id=acceptance.supplier_id,
                        transaction_type=SupplierTransaction.TransactionType.PURCHASE,
                        description=f"Acceptance #{acceptance.id}"
                    ).first()
                    
                    if purchase_txn:
                        purchase_txn.amount = new_debt # Update to the new total debt for this acceptance
                        purchase_txn.save(update_fields=["amount"])
                    else:
                        # This case should ideally not happen if an acceptance was accepted
                        SupplierTransaction.objects.create(
                            supplier_id=acceptance.supplier_id,
                            transaction_type=SupplierTransaction.TransactionType.PURCHASE,
                            amount=new_debt,
                            description=f"Acceptance #{acceptance.id} (created on update)"
                        )

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
