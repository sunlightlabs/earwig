from django.shortcuts import render
from django.conf import settings

from ...models import (MessageResponseStatistic)


def overview(request):
    listing = MessageResponseStatistic.objects.all()

    return render(request, 'contact/admin/statistics/overview.html', {
        "responses": listing,
        "MessageResponseStatistic": MessageResponseStatistic,
        "statistics": MessageResponseStatistic.get_statistics_breakdown_by_template()
    })
