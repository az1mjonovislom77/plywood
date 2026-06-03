
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0002_supplier_company'),
    ]

    operations = [
        migrations.AlterField(
            model_name='suppliertransaction',
            name='transaction_type',
            field=models.CharField(choices=[('purchase', 'Purchase'), ('payment', 'Payment'), ('adjustment', 'Adjustment')], max_length=20),
        ),
    ]
