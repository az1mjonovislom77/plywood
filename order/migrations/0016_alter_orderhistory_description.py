
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0015_orderhistory_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderhistory',
            name='description',
            field=models.TextField(blank=True, max_length=500, null=True),
        ),
    ]
