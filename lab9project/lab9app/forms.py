from django import forms
from .models import Products

class ProductForm(forms.Form):
    CATEGORY_CHOICES = [
        ('GENERAL_MERCHANDISE', 'General Merchandise'),
        ('FOOD_BEVERAGE', 'Food & Beverage'),
    ]

    proname = forms.CharField(label="", max_length=200, widget=forms.TextInput())
    brand = forms.CharField(label="", max_length=200, required=False, widget=forms.TextInput())
    cost = forms.DecimalField(label="", max_digits=10, decimal_places=2, required=False, widget=forms.NumberInput())
    price = forms.DecimalField(label="", max_digits=10, decimal_places=2, widget=forms.NumberInput())
    prodescription = forms.CharField(
        label="", widget=forms.Textarea(attrs={"rows": 3}), required=False
    )
    category = forms.ChoiceField(
        label="", choices=CATEGORY_CHOICES, widget=forms.Select(attrs={"onchange": "toggleFields()"})
    )
    image = forms.CharField(label="", max_length=500, required=False, widget=forms.TextInput())
    quantity_available = forms.IntegerField(label="", required=False, widget=forms.NumberInput())

    # Additional fields
    color = forms.CharField(label="", max_length=20, required=False, widget=forms.TextInput())
    sell_by = forms.DateField(label="", widget=forms.DateInput(attrs={"type": "date"}), required=False)

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")

        if category == "GENERAL_MERCHANDISE" and not cleaned_data.get("color"):
            raise forms.ValidationError("Color is required for General Merchandise.")

        if category == "FOOD_BEVERAGE" and not cleaned_data.get("sell_by"):
            raise forms.ValidationError("Sell By date is required for Food & Beverage.")

        return cleaned_data
