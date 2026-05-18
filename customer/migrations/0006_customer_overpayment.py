from decimal import Decimal

from django.db import migrations, models


def move_negative_debt_to_overpayment(apps, schema_editor):
    Customer = apps.get_model("customer", "Customer")

    for customer in Customer.objects.filter(debt__lt=0):
        customer.overpayment = abs(customer.debt)
        customer.debt = Decimal("0.00")
        customer.save(update_fields=["debt", "overpayment"])


def move_overpayment_back_to_negative_debt(apps, schema_editor):
    Customer = apps.get_model("customer", "Customer")

    for customer in Customer.objects.filter(overpayment__gt=0, debt=0):
        customer.debt = -customer.overpayment
        customer.overpayment = Decimal("0.00")
        customer.save(update_fields=["debt", "overpayment"])


class Migration(migrations.Migration):

    dependencies = [
        ("customer", "0005_alter_balancehistory_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="overpayment",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.RunPython(
            move_negative_debt_to_overpayment,
            move_overpayment_back_to_negative_debt,
        ),
    ]
