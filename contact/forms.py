from django import forms
from .models import FeedbackType


choices = FeedbackType.choices


class FlaggingForm(forms.Form):
    feedback_type = forms.ChoiceField(choices=choices)
    note = forms.CharField(widget=forms.Textarea, required=False)
