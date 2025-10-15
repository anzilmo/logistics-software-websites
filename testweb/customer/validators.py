# validators.py
from django.core.exceptions import ValidationError

def validate_file_size(value):
    """
    Validates that the uploaded file is less than 5 MB.
    """
    limit_mb = 5
    if value.size > limit_mb * 1024 * 1024:
        raise ValidationError(f"File too large. Maximum size allowed is {limit_mb} MB.")
