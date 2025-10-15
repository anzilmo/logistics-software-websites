from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Shipment
from customer.models import Profile






def positive_validator(value):
    """Ensure dimensions/weight are positive numbers."""
    if value is None or value <= 0:
        raise ValidationError(_("Value must be greater than zero."))

# warehouse/forms.py
from decimal import Decimal
from django import forms
from django.core.validators import MinValueValidator
from .models import Shipment

# simple >0 validator
positive_validator = MinValueValidator(Decimal("0.0001"), message="Must be greater than 0")

class ShipmentForm(forms.ModelForm):
    # show but never let users edit it; optional so creates don't fail
    suit_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    length_cm = forms.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[positive_validator],
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        help_text="Length in cm",
    )
    width_cm = forms.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[positive_validator],
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        help_text="Width in cm",
    )
    height_cm = forms.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[positive_validator],
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        help_text="Height in cm",
    )
    weight_kg = forms.DecimalField(
        max_digits=8, decimal_places=3,
        validators=[positive_validator],
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        help_text="Weight in kg",
    )

    class Meta:
        model = Shipment
        fields = [
            "profile",
            "tracking_number",
            "length_cm",
            "width_cm",
            "height_cm",
            "weight_kg",
            "package_type",
            "arrival_date",
            "warehouse",
        ]
        widgets = {
            "tracking_number":  forms.TextInput(attrs={"class": "form-control"}),
            "package_type":     forms.TextInput(attrs={"class": "form-control"}),  # swap to Select if it's a ChoiceField
            "arrival_date":     forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "profile":          forms.Select(attrs={"class": "form-control"}),
        }

  
    def clean_suit_number(self):
        """
        Never allow changes via the form. On create, return whatever the model
        will set (usually None so model auto-generates).
        """
        if self.instance and self.instance.pk:
            return self.instance.suit_number
        return getattr(self.instance, "suit_number", None)

    def clean(self):
        data = super().clean()
        # double-down on >0 in case validators were bypassed
        for f in ("length_cm", "width_cm", "height_cm", "weight_kg"):
            v = data.get(f)
            if v is not None and v <= 0:
                self.add_error(f, "Must be greater than 0")
        return data
