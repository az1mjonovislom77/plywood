
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_product_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='arrival_date',
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]
