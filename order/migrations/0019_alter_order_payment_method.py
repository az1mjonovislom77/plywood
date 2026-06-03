
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0018_alter_order_covered_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('cash', 'Cash'), ('card', 'Card'), ('nasiya', 'Nasiya')], default='cash', max_length=20),
        ),
    ]
