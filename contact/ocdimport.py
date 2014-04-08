import requests
from django.conf import settings
from .models import Person, ContactDetail, ContactType


OCD_API_BASE = settings.OCD_API_BASE
OCD_API_KEY = settings.OCD_API_KEY



def sync_updated_people(since):
    """
    Query the OCD API for people who have been updated since the last run,
    and issue an `import_ocd_person` for each one.
    """
    pass

    for person in iterpeople():


def import_ocd_person(ocd_id):
    """
    Import a person by OCD-ID into the Earwig DB. This needs to be run in
    order to send a message, since the MessageRecipiant has a FK relation
    to a person. This will insert (or update) a single person by OCD ID.
    """

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
    choices = {x[0] for x in ContactType.choices}
    saved_cd = False

    for detail in cds:
        type, value = [detail.get(x) for x in ['type', 'value']]
        if type not in choices:
            continue

        kwargs = {"type": type, "value": value,}
        try:
            cd = ContactDetail.objects.get(**kwargs)
        except ContactDetail.DoesNotExist:
            cd = ContactDetail.objects.create(person=person, **kwargs)

        if detail.get("note"):
            cd.note = detail['note']

        cd.save()
