from django.db import migrations, models


def copy_thickness_price(apps, schema_editor):
    banding_model = apps.get_model("order", "Banding")

    for banding in banding_model.objects.select_related("thickness").filter(thickness__isnull=False):
        banding.thickness_value = banding.thickness.price
        banding.save(update_fields=["thickness_value"])


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0029_orderitem_new_price_in_dollar"),
    ]

    operations = [
        migrations.AddField(
            model_name="banding",
            name="thickness_value",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.RunPython(copy_thickness_price, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="banding",
            name="thickness",
        ),
        migrations.RenameField(
            model_name="banding",
            old_name="thickness_value",
            new_name="thickness",
        ),
    ]
