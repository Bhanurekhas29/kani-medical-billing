from django.db import models
# GST_CHOICES = [
#     (0, '0%'),
#     (5, '5%'),
#     (12, '12%'),
#     (18, '18%'),
#     (28, '28%'),
# ]

# STATE_CHOICES = [
#     ('TN', 'Tamil Nadu'),
#     ('KA', 'Karnataka'),
#     ('KL', 'Kerala'),
#     ('MH', 'Maharashtra'),
#     ('DL', 'Delhi'),
# ]

# class Product(models.Model):
#     batch_no = models.CharField(max_length=100)
#     name = models.CharField(max_length=200)
#     description = models.TextField()

#     # 🆕 Price fields
#     box_price = models.DecimalField(max_digits=10, decimal_places=2) 
#     strip_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     piece_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

#     # 🆕 New fields
#     no_of_strips = models.IntegerField(default=0)  
#     no_of_boxes = models.IntegerField(default=0)

#     expiry_date = models.DateField()
#     stock = models.IntegerField()
#     hsn = models.CharField(max_length=50)

#     gst_percent = models.IntegerField(choices=GST_CHOICES, default=18)
#     state = models.CharField(max_length=2, choices=STATE_CHOICES, default='TN')

#     cgst = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
#     sgst = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
#     igst = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
#     mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

#     def save(self, *args, **kwargs):
#         gst_value = self.gst_percent or 0
#         if self.state == 'TN':
#             self.cgst = gst_value / 2
#             self.sgst = gst_value / 2
#             self.igst = 0
#         else:
#             self.cgst = 0
#             self.sgst = 0
#             self.igst = gst_value

#         # ✅ Calculate MRP (based on piece price)
#         self.mrp = round(self.piece_price + (self.piece_price * gst_value / 100), 2)

#         super(Product, self).save(*args, **kwargs)
    

#     def __str__(self):
#         return f"{self.name} ({self.batch_no})"

# accounts/models.py
from django.db import models

# GST_CHOICES = [(0,'0%'),(5,'5%'),(12,'12%'),(18,'18%'),(28,'28%')]
# STATE_CHOICES = [('TN','Tamil Nadu'),('KA','Karnataka'),('KL','Kerala'),('MH','Maharashtra'),('DL','Delhi')]

# class Product(models.Model):
#     batch_no    = models.CharField(max_length=100)
#     name        = models.CharField(max_length=200)
#     description = models.TextField(blank=True)

#     # Prices per unit
#     box_price   = models.DecimalField(max_digits=10, decimal_places=2)
#     strip_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     piece_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

#     # Composition: how many strips per box, how many pieces per strip
#     # (Use your existing names, as you requested)
#     no_of_boxes  = models.IntegerField(default=0)  # strips per box
#     no_of_strips = models.IntegerField(default=0)  # pieces per strip

#     expiry_date = models.DateField()

#     # Stock per unit
#     box_stock   = models.IntegerField(default=0)
#     strip_stock = models.IntegerField(default=0)
#     stock       = models.IntegerField(default=0)  # pieces

#     hsn         = models.CharField(max_length=50, blank=True)
#     gst_percent = models.IntegerField(choices=GST_CHOICES, default=18)
#     state       = models.CharField(max_length=2, choices=STATE_CHOICES, default='TN')

#     # tax split for reference
#     cgst = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
#     sgst = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
#     igst = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

#     # Optional: keep piece MRP if you want (not used in calculations)
#     mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

#     def price_for(self, unit_type: str) -> float:
#         if unit_type == 'box':
#             return float(self.box_price)
#         if unit_type == 'strip':
#             return float(self.strip_price)
#         return float(self.piece_price)

#     def mrp_for(self, unit_type: str) -> float:
#         base = self.price_for(unit_type)
#         return round(base + (base * (self.gst_percent or 0) / 100.0), 2)

#     def available_for(self, unit_type: str) -> int:
#         if unit_type == 'box':
#             return int(self.box_stock)
#         if unit_type == 'strip':
#             return int(self.strip_stock)
#         return int(self.stock)

#     def apply_sale(self, unit_type: str, qty: int):
#         """Decrease stocks for unit and derived units."""
#         qty = int(qty or 0)
#         if qty <= 0:
#             return

#         if unit_type == 'piece':
#             self.stock = max(0, self.stock - qty)

#         elif unit_type == 'strip':
#             # strip stock
#             self.strip_stock = max(0, self.strip_stock - qty)
#             # pieces implied by strips
#             pieces_down = qty * max(0, self.no_of_strips)
#             self.stock = max(0, self.stock - pieces_down)

#         elif unit_type == 'box':
#             # box stock
#             self.box_stock = max(0, self.box_stock - qty)
#             # strips implied by boxes
#             strips_down = qty * max(0, self.no_of_boxes)  # no_of_boxes = strips per box
#             self.strip_stock = max(0, self.strip_stock - strips_down)
#             # pieces implied by those strips
#             pieces_down = strips_down * max(0, self.no_of_strips)  # no_of_strips = pieces per strip
#             self.stock = max(0, self.stock - pieces_down)

#     def save(self, *args, **kwargs):
#         gst_value = self.gst_percent or 0
#         if self.state == 'TN':
#             self.cgst = gst_value / 2
#             self.sgst = gst_value / 2
#             self.igst = 0
#         else:
#             self.cgst = 0
#             self.sgst = 0
#             self.igst = gst_value

#         # Keep a reference piece MRP if needed
#         self.mrp = round(float(self.piece_price) + (float(self.piece_price) * gst_value / 100.0), 2)
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.name} ({self.batch_no})"

# models.py
from django.db import models

GST_CHOICES = [(0,'0%'),(5,'5%'),(12,'12%'),(18,'18%'),(28,'28%')]
STATE_CHOICES = [
    ('TN','Tamil Nadu'),
    ('KA','Karnataka'),
    ('KL','Kerala'),
    ('MH','Maharashtra'),
    ('DL','Delhi')
]

class Product(models.Model):
    batch_no    = models.CharField(max_length=100)
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Prices per unit
    box_price   = models.DecimalField(max_digits=10, decimal_places=2)
    strip_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    piece_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    expiry_date = models.DateField()

    # Composition (conversions)
    strips_per_box   = models.IntegerField(default=0)   # how many strips in a box
    pieces_per_strip = models.IntegerField(default=0)   # how many pieces in a strip

    # Stock per unit
    box_stock   = models.IntegerField(default=0)
    strip_stock = models.IntegerField(default=0)
    piece_stock = models.IntegerField(default=0)        # ← renamed from `stock`

    hsn         = models.CharField(max_length=50, blank=True)
    gst_percent = models.IntegerField(choices=GST_CHOICES, default=18)
    state       = models.CharField(max_length=2, choices=STATE_CHOICES, default='TN')

    # tax split for reference
    cgst = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    sgst = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    igst = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    # Optional: convenience MRP for one piece
    mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # ---------- Helpers ----------
    def price_for(self, unit_type: str) -> float:
        if unit_type == 'box':
            return float(self.box_price)
        if unit_type == 'strip':
            return float(self.strip_price)
        return float(self.piece_price)

    def mrp_for(self, unit_type: str) -> float:
        base = self.price_for(unit_type)
        return round(base + (base * (self.gst_percent or 0) / 100.0), 2)

    def available_for(self, unit_type: str) -> int:
        if unit_type == 'box':
            return int(self.box_stock)
        if unit_type == 'strip':
            return int(self.strip_stock)
        return int(self.piece_stock)

    def apply_sale(self, unit_type: str, qty: int):
        """
        Decrease stocks for the sold unit AND its derived units.
        This is called only when an invoice is finalized.
        """
        qty = int(qty or 0)
        if qty <= 0:
            return

        if unit_type == 'piece':
            self.piece_stock = max(0, self.piece_stock - qty)

        elif unit_type == 'strip':
            self.strip_stock = max(0, self.strip_stock - qty)
            pieces_down = qty * max(1, self.pieces_per_strip)
            self.piece_stock = max(0, self.piece_stock - pieces_down)

        elif unit_type == 'box':
            self.box_stock = max(0, self.box_stock - qty)
            strips_down = qty * max(1, self.strips_per_box)
            self.strip_stock = max(0, self.strip_stock - strips_down)
            pieces_down = strips_down * max(1, self.pieces_per_strip)
            self.piece_stock = max(0, self.piece_stock - pieces_down)

    def save(self, *args, **kwargs):
        # tax split
        gst_value = float(self.gst_percent or 0)
        if self.state == 'TN':
            self.cgst = gst_value / 2
            self.sgst = gst_value / 2
            self.igst = 0
        else:
            self.cgst = 0
            self.sgst = 0
            self.igst = gst_value

        # convenience: piece MRP
        self.mrp = round(float(self.piece_price) + (float(self.piece_price) * gst_value / 100.0), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.batch_no})"

# models.py

from django.db import models
from django.utils import timezone

# class Invoice(models.Model):
#     invoice_number = models.CharField(max_length=50, unique=True)
#     invoice_date = models.DateField(default=timezone.now)
#     from_name = models.CharField(max_length=255)
#     from_phone = models.CharField(max_length=20)
#     from_address = models.TextField()
#     to_name = models.CharField(max_length=255)
#     to_phone = models.CharField(max_length=20)
#     to_address = models.TextField()
#     dl_no = models.CharField(max_length=100)
#     license_no = models.CharField(max_length=100)
#     total = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"Invoice {self.invoice_number}"


# class InvoiceItem(models.Model):
#     invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
#     product = models.ForeignKey('Product', on_delete=models.CASCADE)
#     batch_no = models.CharField(max_length=100)
#     mrp = models.DecimalField(max_digits=10, decimal_places=2)
#     quantity = models.IntegerField()
#     subtotal = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"{self.product.name} - {self.quantity}"

from datetime import date

class Invoice(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField(default=timezone.now)
    from_name = models.CharField(max_length=255)
    from_phone = models.CharField(max_length=20)
    from_address = models.TextField()
    to_name = models.CharField(max_length=255)
    to_phone = models.CharField(max_length=20)
    to_address = models.TextField()
    dl_no = models.CharField(max_length=100)
    # license_no = models.CharField(max_length=100)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Invoice {self.invoice_number}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch_no = models.CharField(max_length=100)
    expiry_date = models.DateField(default=date.today)  # ✅ add this line
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    unit_type = models.CharField(max_length=10, default='piece') 

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()

    def __str__(self):
        return self.name
