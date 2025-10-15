import os
from django import forms
from .models import PurchaseBill, Plan, Membership, MembershipTier, MembershipApplication

class PurchaseBillForm(forms.ModelForm):
    class Meta:
        model = PurchaseBill
        fields = ('supplier', 'invoice_number', 'date', 'amount', 'pdf')

    def clean_pdf(self):
        pdf = self.cleaned_data.get('pdf')
        if pdf:
            ext = os.path.splitext(pdf.name)[1].lower()
            if ext != '.pdf':
                raise forms.ValidationError("Only PDF files are allowed.")
        return pdf



# forms.py
from django import forms
from django.core.validators import RegexValidator


E164_VALIDATOR = RegexValidator(r"^\+?[1-9]\d{1,14}$", "Use E.164 like +97455555555")




class MembershipApplicationForm(forms.Form):
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(active=True),
        empty_label="Select a plan",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Membership Plan"
    )
    billing_cycle = forms.ChoiceField(
        choices=Plan.BILLING_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Billing Cycle"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optionally, filter plans or add more logic


class SelectMembershipForm(forms.Form):
    tier = forms.ModelChoiceField(queryset=MembershipTier.objects.filter(active=True)
                                  .order_by("ordering", "name"), required=True, label="Membership tier")


class MembershipApplicationForm(forms.ModelForm):
    class Meta:
        model = MembershipApplication
        fields = ["plan", "billing_cycle"]
        widgets = {
            "plan": forms.Select(attrs={"class": "form-select"}),
            "billing_cycle": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plan"].queryset = Plan.objects.filter(active=True)



class SubscriptionForm(forms.Form):
    # Plan selection
    plan = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect,
        label="Choose Plan"
    )

    # Account details
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    company = forms.CharField(max_length=100, required=False)

    # Billing Address
    address1 = forms.CharField(max_length=255, required=True, label="Address line 1")
    address2 = forms.CharField(max_length=255, required=False, label="Address line 2")
    city = forms.CharField(max_length=120, required=True)
    state = forms.CharField(max_length=120, required=True, label="State/Province")
    zip = forms.CharField(max_length=32, required=True, label="ZIP/Postal code")
    country = forms.ChoiceField(
        choices=[
            ('US', 'United States'),
            ('CA', 'Canada'),
            ('GB', 'United Kingdom'),
            ('QA', 'Qatar'),
            ('AE', 'United Arab Emirates'),
            ('IN', 'India'),
            ('DE', 'Germany'),
            ('FR', 'France'),
        ],
        required=True
    )

    # Payment Method
    payment = forms.ChoiceField(
        choices=[('card', 'Card'), ('paypal', 'PayPal')],
        widget=forms.RadioSelect,
        initial='card',
        label="Payment Method"
    )

    # Card details (only if payment=card)
    card_number = forms.CharField(max_length=19, required=False, label="Card number")
    exp = forms.CharField(max_length=5, required=False, label="Expiry")
    cvc = forms.CharField(max_length=4, required=False, label="CVC")
    name_on_card = forms.CharField(max_length=100, required=False, label="Name on card")

    # Agreement
    agree = forms.BooleanField(required=True, label="I agree to the Terms and Privacy Policy.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate plan choices from MembershipTier
        tiers = MembershipTier.objects.filter(active=True).order_by('ordering')
        choices = []
        for tier in tiers:
            price = 9 if tier.name == 'Silver' else 29 if tier.name == 'Gold' else 79
            label = f"{tier.name} — ${price}/mo"
            choices.append((tier.name.lower(), label))
        self.fields['plan'].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        payment = cleaned_data.get('payment')
        if payment == 'card':
            required_card_fields = ['card_number', 'exp', 'cvc', 'name_on_card']
            for field in required_card_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, 'This field is required for card payment.')
        return cleaned_data





from django import forms

class DeliveryAddressForm(forms.Form):
    recipient_name = forms.CharField(max_length=255, label="Recipient name")
    address_line1 = forms.CharField(max_length=255, label="Address line 1")
    address_line2 = forms.CharField(max_length=255, required=False, label="Address line 2")
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100, required=False)
    postal_code = forms.CharField(max_length=32, required=False)
    country = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=40, required=False)

class PaymentForm(forms.Form):
    PAYMENT_CHOICES = [
        ("card", "Credit / Debit Card"),
        ("offline", "Offline / Bank Transfer"),
    ]
    payment_method = forms.ChoiceField(choices=PAYMENT_CHOICES, widget=forms.RadioSelect, initial="card")
    # For card payments you should use a tokenization flow (Stripe Elements etc.)
    # Here we accept a dummy token for demo purposes:
    card_token = forms.CharField(max_length=255, required=False, help_text="Use a token from your payment provider (demo)")

    # Optional billing fields
    billing_name = forms.CharField(max_length=255, required=False)
    billing_email = forms.EmailField(required=False)
    
    
    
    
    
    
    
    
from django import forms

class TrackingLookupForm(forms.Form):
    """
    Simple form to allow a customer to enter a tracking number or suit number.
    """
    query = forms.CharField(
        max_length=255,
        label="Tracking number or Suit number",
        widget=forms.TextInput(attrs={"placeholder": "Enter tracking number or suit number"})
    )


from django import forms
from .models import ConsoleShipment

class ConsoleShipmentForm(forms.Form):
    action = forms.ChoiceField(choices=ConsoleShipment.ACTION_CHOICES, label="Action")
    note = forms.CharField(max_length=2000, required=False, widget=forms.Textarea(attrs={'rows': 3}), label="Note")

class BulkActionForm(forms.Form):
    action = forms.ChoiceField(choices=ConsoleShipment.ACTION_CHOICES, label="Action")

class BulkAssignCourierForm(forms.Form):
    rate_id = forms.IntegerField(label="Courier Rate ID")



