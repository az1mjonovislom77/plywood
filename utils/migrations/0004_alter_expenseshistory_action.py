
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0003_expenses_expenseshistory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenseshistory',
            name='action',
            field=models.CharField(choices=[('created', 'Created'), ('accept', 'Accept'), ('cancel', 'Cancel')], max_length=10),
        ),
    ]
