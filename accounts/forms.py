from django import forms
from .models import Product

# class ProductForm(forms.ModelForm):
#     class Meta:
#         model = Product
        
#         widgets = {
#             'expiry_date': forms.DateInput(attrs={'type': 'date'}),
#             'description': forms.Textarea(attrs={'rows': 2}),
#         }

# accounts/forms.py
from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'batch_no','name','description','expiry_date',
            'box_price','strip_price','piece_price',
            'strips_per_box','pieces_per_strip',
            'gst_percent','hsn','state',
            'box_stock','strip_stock','piece_stock',  # stock per unit
            
        ]
        exclude = ['cgst', 'sgst', 'igst', 'mrp']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }
