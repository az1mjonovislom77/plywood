
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0014_product_sale_price_in_dollar'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='arrival_price_in_dollar',
        ),
        migrations.RemoveField(
            model_name='product',
            name='sale_price_in_dollar',
        ),
        migrations.AddField(
            model_name='product',
            name='arrival_price_in_sum',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=15, verbose_name='Arrival Price in UZS'),
        ),
        migrations.AddField(
            model_name='product',
            name='sale_price_in_sum',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=15, verbose_name='Sale Price in UZS'),
        ),
        migrations.AlterField(
            model_name='product',
            name='arrival_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Arrival Price in USD'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sale_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Sale Price in USD'),
        ),
    ]
