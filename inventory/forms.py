# inventory/forms.py
from django import forms
from .models import Product, PurchaseOrder, PurchaseItem, Supplier, Customer, StockAdjustment

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

# In inventory/forms.py, update or add these forms:
class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'expected_date', 'notes']
        widgets = {
            'expected_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter any notes or special instructions...'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
        }

class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ['product', 'quantity', 'unit_cost']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

# In inventory/forms.py, make sure CustomerForm has this:
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'name': forms.TextInput(attrs={'placeholder': 'Enter customer name'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email address'}),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Clean phone number (remove spaces, dashes, etc.)
            phone = phone.replace(' ', '').replace('-', '').replace('+', '')
            
            # Check if phone number already exists (excluding current instance)
            if self.instance.pk:
                existing = Customer.objects.filter(phone=phone).exclude(pk=self.instance.pk)
            else:
                existing = Customer.objects.filter(phone=phone)
            
            if existing.exists():
                raise forms.ValidationError('A customer with this phone number already exists.')
        
        return phone

# Optional: Update the StockAdjustmentForm to include common reasons
class StockAdjustmentForm(forms.ModelForm):
    COMMON_REASONS = [
        ('', 'Select a reason or type custom...'),
        ('damaged', 'Damaged Goods'),
        ('return', 'Customer Return'),
        ('found', 'Found Stock'),
        ('theft', 'Theft/Loss'),
        ('sample', 'Sample/Demo'),
        ('donation', 'Donation'),
        ('quality_control', 'Quality Control'),
        ('expired', 'Expired Product'),
        ('counting_error', 'Counting Error'),
    ]
    
    reason = forms.ChoiceField(
        choices=COMMON_REASONS,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    custom_reason = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control mt-2',
            'placeholder': 'Or enter custom reason...',
            'style': 'display: none;'
        })
    )
    
    class Meta:
        model = StockAdjustment
        fields = ['product', 'adjustment_type', 'quantity', 'reason', 'notes']
        # ... rest of the Meta class ...
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom_reason field to the form
        self.fields['custom_reason'] = forms.CharField(
            required=False,
            max_length=200,
            widget=forms.TextInput(attrs={
                'class': 'form-control mt-2',
                'placeholder': 'Or enter custom reason...',
                'style': 'display: none;'
            })
        )
    
    def clean(self):
        cleaned_data = super().clean()
        reason = cleaned_data.get('reason')
        custom_reason = cleaned_data.get('custom_reason')
        
        # If custom reason is provided, use it instead
        if custom_reason:
            cleaned_data['reason'] = custom_reason
        
        return cleaned_data