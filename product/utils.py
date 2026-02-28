from django.core.exceptions import ValidationError


def check_image_size(image):
    if image.size > 10 * 1024 * 1024:
        raise ValidationError("The image is too long")
