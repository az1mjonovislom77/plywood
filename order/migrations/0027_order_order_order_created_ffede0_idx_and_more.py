
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0005_alter_balancehistory_type'),
        ('order', '0026_alter_banding_discount_type_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['created_at'], name='order_order_created_ffede0_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['customer', 'created_at'], name='order_order_custome_a09334_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['user', 'created_at'], name='order_order_user_id_55dcc8_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['order_status'], name='order_order_order_s_54575a_idx'),
        ),
        migrations.AddIndex(
            model_name='orderhistory',
            index=models.Index(fields=['order', '-created_at'], name='order_order_order_i_5a04bb_idx'),
        ),
    ]
