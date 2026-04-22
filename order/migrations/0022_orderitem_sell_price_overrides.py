import django.db.models.deletion
from django.db import migrations, models
from django.db.models import F


def populate_original_sell_price(apps, schema_editor):
    order_item = apps.get_model("order", "OrderItem")
    order_item.objects.filter(original_sell_price=0).update(original_sell_price=F("price"))


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0021_banding_cutting_payment_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="original_sell_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="banding",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="order_items", to="order.banding"),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="cutting",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="order_items", to="order.cutting"),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="new_sell_price",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="sell_price_difference",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.RunPython(populate_original_sell_price, migrations.RunPython.noop),
    ]
