
from django import forms
from django.db import models

from .. import mixins, widgets


class Answer(models.IntegerChoices):
    NO = (0, 'No')
    YES = (1, 'Yes')


class DateInput(forms.DateInput):
    input_type = 'date'


class SampleForm(mixins.AsDiv2, forms.Form):
    """
    Form to exercise the BoundFieldRenderer with many different widgets.
    """
    name = forms.CharField(
        help_text="Put your name in here. Just like on an exam.",
    )
    answer = forms.ChoiceField(
        choices=[('', '')] + Answer.choices,                # type: ignore[operator]
        help_text="Only two choices here - but only one is correct.",
    )
    answer2 = forms.ChoiceField(
        choices=Answer.choices,
        widget=forms.RadioSelect(),
        help_text="Here, let me lay 'em out for you.",
    )
    time = forms.TimeField(
        widget=widgets.TimeWidget(start='07:00', end='18:00'),
    )
    date = forms.DateField(
        widget=DateInput(),
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 5}),
        help_text="Lay out your thoughts. The process can be cathartic.",
    )
    subscribe = forms.BooleanField(
        help_text="May we collect your information, then bombard you with emails?",
    )
