
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acceptance', '0005_alter_acceptance_supplier'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acceptance',
            name='arrival_date',
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]
