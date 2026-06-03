
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acceptance', '0014_alter_acceptance_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='acceptance',
            name='sale_price_in_dollar',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
