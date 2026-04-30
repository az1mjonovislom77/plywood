from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0027_order_order_order_created_ffede0_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='exchange_rate',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='price_in_dollar',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True),
        ),
    ]
