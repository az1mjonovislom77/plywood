from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("acceptance", "0009_alter_acceptance_count"),
    ]

    operations = [
        migrations.AlterField(
            model_name="acceptancehistory",
            name="count",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
        ),
    ]
