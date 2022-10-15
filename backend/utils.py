import datetime
from typing import Union

import arrow
from django.utils import timezone
from rest_framework.exceptions import ValidationError


def parse_ids(model, id_list: list) -> list:
    items = model.objects.all()

    # Get and validate list of plant IDs
    if id_list:
        try:
            id_list = list(map(int, id_list))
        except ValueError:
            raise ValidationError('IDs must be integer values')
        valid_ids = items.filter(id__in=id_list).values_list('id', flat=True)
        invalid_ids = set(id_list) - set(valid_ids)
        if invalid_ids:
            raise ValidationError(f'Invalid IDs: {invalid_ids}')
    else:
        id_list = items.values_list('id', flat=True)
    return id_list


def parse_date(date_str: str) -> Union[datetime.date, None]:
    date = None
    if date_str:
        try:
            date = arrow.get(date_str).date()
        except:
            raise ValidationError(f"Invalid date: '{date_str}'.")
        if date > timezone.now().date():
            raise ValidationError(f"Date '{date_str}' is from the future.")
    return date
