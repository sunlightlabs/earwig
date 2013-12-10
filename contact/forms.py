from django import forms
from .models import FEEDBACK_TYPES


FEEDBACK_TYPES = filter(lambda x: x[0] != 'vendor', FEEDBACK_TYPES)

class FlaggingForm(forms.Form):
    feedback_type = forms.ChoiceField(choices=FEEDBACK_TYPES)
    note = forms.CharField(widget=forms.Textarea, required=False)