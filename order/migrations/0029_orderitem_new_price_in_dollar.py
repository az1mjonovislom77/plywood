from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0028_orderitem_exchange_rate_price_in_dollar"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="new_price_in_dollar",
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True),
        ),
    ]
