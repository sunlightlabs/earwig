from django.shortcuts import render
from django.conf import settings

from ...models import (MessageResponseStatistic, MessageResponseStatisticTypes)


def overview(request):
    listing = MessageResponseStatistic.objects.all()

    return render(request, 'contact/admin/statistics/overview.html', {
        "responses": listing,
        "MessageResponseStatistic": MessageResponseStatistic,
        "statistics": MessageResponseStatistic.get_statistics_breakdown_by_template()
    })


def overview_template(request, template):

    value = MessageResponseStatistic.get_statistics_by_template(
        template, limit=100)

    breakdown = {
        x: 0 for x in [
            y[0] for y in MessageResponseStatisticTypes.choices
        ]
    }

    for statistic in value:
        breakdown[statistic.message_feedback] += 1

    return render(request, 'contact/admin/statistics/template.html', {
        "template": template,
        "statistics": value,
        "breakdown": breakdown,
    })
