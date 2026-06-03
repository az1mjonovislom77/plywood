
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acceptance', '0016_alter_acceptance_arrival_price_in_dollar_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acceptancehistory',
            name='action',
            field=models.CharField(choices=[('create', 'Create'), ('update', 'Update'), ('accept', 'Accept'), ('cancel', 'Cancel')], max_length=20),
        ),
    ]
