from rest_framework import serializers
from customer.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "full_name", "phone_number", "location", "debt", "about", "description"]
        read_only_fields = ["debt"]
