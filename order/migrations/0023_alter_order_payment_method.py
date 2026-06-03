
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0022_orderitem_sell_price_overrides'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('cash', 'Naqd'), ('card', 'Karta'), ('nasiya', 'Nasiya')], default='cash', max_length=20),
        ),
    ]
