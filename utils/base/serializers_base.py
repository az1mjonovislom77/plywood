from rest_framework import serializers


class TrimmedDecimalField(serializers.DecimalField):
    def to_representation(self, value):
        if value is None:
            return None

        value = super().to_representation(value)
        value = str(value)

        if "." not in value:
            return value

        return value.rstrip("0").rstrip(".")


class BaseReadSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        fields = "__all__"
