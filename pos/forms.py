# pos/forms.py
from django import forms
from .models import Sale, SaleItem
from inventory.models import Product, Customer

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer', 'discount_amount', 'payment_method', 'payment_received', 'notes']

class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show products that have stock
        self.fields['product'].queryset = Product.objects.filter(
            track_stock=False
        ) | Product.objects.filter(
            track_stock=True, current_stock__gt=0
        )