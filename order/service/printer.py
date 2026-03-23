from escpos.printer import Usb
from django.conf import settings

WIDTH = 28


def line(left, right):
    left = str(left)[:20]
    right = str(right)
    return left.ljust(20) + right.rjust(12)


def money(val):
    return f"{int(val.quantize(0)):,}".replace(",", " ")


def print_receipt(order):
    try:
        p = Usb(settings.USB_PRINTER_VENDOR_ID, settings.USB_PRINTER_PRODUCT_ID)

        p.set(align='center', bold=True, width=2, height=2)
        p.text("CHEK\n")

        p.set(align='left')
        p.text("-" * WIDTH + "\n")

        p.text(f"Buyurtma: #{order.id}\n")
        p.text(f"Sana: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n")

        if order.is_anonymous or not order.customer:
            p.text("Mijoz: ANONIM\n")
        else:
            p.text(f"Mijoz: {order.customer}\n")

        p.text("-" * WIDTH + "\n")

        for item in order.items.all():
            p.text(line(item.product.name, f"{item.quantity}x{money(item.price)}") + "\n")

        p.text("-" * WIDTH + "\n")

        p.set(bold=True)
        p.text(("JAMI: " + money(order.total_price) + " UZS").center(WIDTH) + "\n")

        p.set(bold=False)
        p.text("\nRahmat!\n\n")

        p.cut()

    except Exception as e:
        print("Printer error:", e)
