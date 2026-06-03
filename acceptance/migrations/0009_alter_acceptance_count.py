
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acceptance', '0008_alter_acceptancehistory_acceptance_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acceptance',
            name='count',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
        ),
    ]
