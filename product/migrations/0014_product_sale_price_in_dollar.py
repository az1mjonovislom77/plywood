
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0013_alter_product_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sale_price_in_dollar',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
