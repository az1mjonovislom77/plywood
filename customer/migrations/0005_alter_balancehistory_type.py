from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customer", "0004_balancehistory_delete_payment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="balancehistory",
            name="type",
            field=models.CharField(
                choices=[
                    ("DEBT_ADD", "Debt Added"),
                    ("PAYMENT", "Debt Payment"),
                    ("ORDER_PAYMENT", "Order Payment"),
                ],
                max_length=20,
            ),
        ),
    ]
