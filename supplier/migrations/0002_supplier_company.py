
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='company',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
