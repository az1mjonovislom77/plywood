
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acceptance', '0015_acceptance_sale_price_in_dollar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acceptance',
            name='arrival_price_in_dollar',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=10),
        ),
        migrations.AlterField(
            model_name='acceptance',
            name='arrival_price_in_sum',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=15),
        ),
        migrations.AlterField(
            model_name='acceptance',
            name='sale_price_in_dollar',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=10),
        ),
        migrations.AlterField(
            model_name='acceptance',
            name='sale_price_in_sum',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=15),
        ),
    ]
