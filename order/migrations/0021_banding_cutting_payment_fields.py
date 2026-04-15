import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customer", "0004_balancehistory_delete_payment"),
        ("order", "0020_alter_cutting_count_alter_orderitem_quantity"),
    ]

    operations = [
        migrations.AddField(
            model_name="banding",
            name="covered_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name="banding",
            name="customer",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name="bandings", to="customer.customer"),
        ),
        migrations.AddField(
            model_name="banding",
            name="discount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="banding",
            name="discount_type",
            field=models.CharField(choices=[("p", "Percentage"), ("c", "Cash")], default="c", max_length=1),
        ),
        migrations.AddField(
            model_name="banding",
            name="payment_method",
            field=models.CharField(choices=[("cash", "Cash"), ("card", "Card"), ("nasiya", "Nasiya")],
                                   default="cash", max_length=20),
        ),
        migrations.AddField(
            model_name="cutting",
            name="covered_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name="cutting",
            name="customer",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name="cuttings", to="customer.customer"),
        ),
        migrations.AddField(
            model_name="cutting",
            name="discount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="cutting",
            name="discount_type",
            field=models.CharField(choices=[("p", "Percentage"), ("c", "Cash")], default="c", max_length=1),
        ),
        migrations.AddField(
            model_name="cutting",
            name="payment_method",
            field=models.CharField(choices=[("cash", "Cash"), ("card", "Card"), ("nasiya", "Nasiya")],
                                   default="cash", max_length=20),
        ),
    ]
