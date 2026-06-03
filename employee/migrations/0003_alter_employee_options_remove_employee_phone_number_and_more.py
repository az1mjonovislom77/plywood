
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0002_remove_employee_balance'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='employee',
            options={},
        ),
        migrations.RemoveField(
            model_name='employee',
            name='phone_number',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='salary',
        ),
        migrations.AddField(
            model_name='employee',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='full_name',
            field=models.CharField(max_length=255),
        ),
        migrations.CreateModel(
            name='SalaryPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('paid_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salary_payments', to='employee.employee')),
                ('paid_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-paid_at'],
            },
        ),
    ]
