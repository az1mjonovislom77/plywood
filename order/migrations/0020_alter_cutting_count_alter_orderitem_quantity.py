
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0019_alter_order_payment_method'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cutting',
            name='count',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='quantity',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
        ),
    ]
