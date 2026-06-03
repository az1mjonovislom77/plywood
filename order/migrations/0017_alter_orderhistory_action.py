
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0016_alter_orderhistory_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderhistory',
            name='action',
            field=models.CharField(choices=[('create', 'Create'), ('accept', 'Accept'), ('cancel', 'Cancel')], max_length=20),
        ),
    ]
