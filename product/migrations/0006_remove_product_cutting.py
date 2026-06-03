
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0005_product_cutting'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='cutting',
        ),
    ]
