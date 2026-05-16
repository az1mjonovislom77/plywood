from rest_framework import serializers
from decimal import Decimal

class TrimmedDecimalField(serializers.DecimalField):
    def to_representation(self, value):
        if value is None:
            return None

        value = Decimal(str(value))

        value = format(value, "f")

        if "." not in value:
            return value

        return value.rstrip("0").rstrip(".")


class BaseReadSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        fields = "__all__"
