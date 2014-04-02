from django import forms
from .models import FeedbackType, MessageResponseStatisticTypes


class FlaggingForm(forms.Form):
    feedback_type = forms.ChoiceField(choices=FeedbackType.choices)
    note = forms.CharField(widget=forms.Textarea, required=False)


class StatisticsForm(forms.Form):
    communication_type = forms.ChoiceField(
        choices=MessageResponseStatisticTypes.choices
    )
