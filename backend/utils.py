import datetime
from typing import Optional, Union

import arrow
import pytz
from django.conf import settings
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


def parse_date(
        date_str: Optional[str],
        as_datetime: bool = False
) -> Optional[Union[datetime.datetime, datetime.date]]:
    date = None
    if date_str:
        try:
            date = arrow.get(
                date_str,
                tzinfo=pytz.timezone(settings.TIME_ZONE)
            ).datetime
        except:
            raise ValidationError(f"Invalid date: '{date_str}'.")
        now = timezone.now()
        if not as_datetime:
            date = date.date()
            now = now.date()
        if date > now:
            raise ValidationError(f"Date '{date_str}' is from the future.")
    return date
