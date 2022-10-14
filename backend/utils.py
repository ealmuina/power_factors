import arrow
from django.utils import timezone
from rest_framework.exceptions import ValidationError


def parse_date(date_str, validate=False):
    date = None
    if date_str:
        try:
            date = arrow.get(date_str).date()
        except:
            raise ValidationError(f"Invalid date: '{date_str}'.")
        if validate and date > timezone.now().date():
            raise ValidationError(f"Date '{date_str}' is from the future.")
    return date
