
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acceptance', '0011_alter_acceptancehistory_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='acceptance',
            name='arrival_price_in_dollar',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
