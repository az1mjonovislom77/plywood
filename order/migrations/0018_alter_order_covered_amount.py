
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0017_alter_orderhistory_action'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='covered_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
    ]
