import requests
import datetime
from django.utils.timezone import utc
from django.conf import settings
from .models import Person, ContactDetail


OCD_API_BASE = settings.OCD_API_BASE
OCD_API_KEY = settings.OCD_API_KEY


def utcnow():
    return datetime.datetime.utcnow().replace(tzinfo=utc)


def import_ocd_person(ocd_id):
    url = "%s/%s?apikey=%s" % (OCD_API_BASE, ocd_id, OCD_API_KEY)
    data = requests.get(url).json()
    title = data.get('title', None)
    photo_url = data.get('photo_url', None)
    cds = data.get("contact_details", [])

    try:
        person = Person.objects.get(ocd_id=ocd_id)
    except Person.DoesNotExist:
        person = Person.objects.create(ocd_id=ocd_id)

    person.name = data['name']

    if title:
        person.title = title

    if photo_url:
        person.photo_url = photo_url

    person.save()

    for detail in cds:
        print(detail)
