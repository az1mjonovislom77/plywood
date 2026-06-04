from django.db.models.signals import pre_save
from django.dispatch import receiver
from utils.models import Services


@receiver(pre_save, sender=Services)
def calculate_services_total_price(sender, instance, **kwargs):
    instance.total_price = instance.calculate_total_price()
