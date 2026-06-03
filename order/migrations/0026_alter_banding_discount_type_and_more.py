
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0025_alter_banding_discount_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='banding',
            name='discount_type',
            field=models.CharField(choices=[('p', 'Foiz'), ('c', 'Naqd')], default='c', max_length=1),
        ),
        migrations.AlterField(
            model_name='banding',
            name='payment_method',
            field=models.CharField(choices=[('cash', 'Naqd'), ('card', 'Kart'), ('nasiya', 'Nasiya')], default='cash', max_length=20),
        ),
        migrations.AlterField(
            model_name='cutting',
            name='discount_type',
            field=models.CharField(choices=[('p', 'Foiz'), ('c', 'Naqd')], default='c', max_length=1),
        ),
        migrations.AlterField(
            model_name='cutting',
            name='payment_method',
            field=models.CharField(choices=[('cash', 'Naqd'), ('card', 'Karta'), ('nasiya', 'Nasiya')], default='cash', max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='discount_type',
            field=models.CharField(choices=[('p', 'Foiz'), ('c', 'Naqd')], default='c', max_length=1),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('cash', 'Naqd'), ('card', 'Karta'), ('nasiya', 'Nasiya')], default='cash', max_length=20),
        ),
    ]
