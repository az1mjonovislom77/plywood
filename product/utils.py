from django.core.exceptions import ValidationError


def check_image_size(image):
    if image.size > 10 * 1024 * 1024:
        raise ValidationError("Rasm hajmi 10 MB dan oshmasligi kerak")


def check_image_content(image):
    ext = image.name.rsplit('.', 1)[-1].lower()
    if ext == 'svg':
        return
    try:
        from PIL import Image
        img = Image.open(image)
        img.verify()
    except Exception:
        raise ValidationError("Yuklangan fayl rasm emas yoki buzilgan")
    finally:
        image.seek(0)
