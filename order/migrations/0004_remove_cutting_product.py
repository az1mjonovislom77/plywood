
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_cutting_product'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cutting',
            name='product',
        ),
    ]
