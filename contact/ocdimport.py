import requests
from django.conf import settings
from .models import Person, ContactDetail, ContactType


OCD_API_BASE = settings.OCD_API_BASE
OCD_API_KEY = settings.OCD_API_KEY


def ocd_iterpeople(since, page=None):
    """
    Query the OCD API for people who have been updated since the last run,
    and issue an `import_ocd_person` for each one.
    """
    if page is None:
        page = 0

    url = "%s/people/?apikey=%s&updated_at__gte=%s&page=%s" % (
        OCD_API_BASE, OCD_API_KEY, since, page,
    )
    data = requests.get(url).json()
    meta, results = [data.get(x) for x in ['meta', 'results']]
    for result in results:
        yield result.get('id')

    if meta['page'] < meta['max_page']:
        yield from ocd_iterpeople(since, page=(page + 1))


def sync_updated_people(since):
    for x in ocd_iterpeople(since):
        import_ocd_person(x)


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
    if data.get('memberships'):
        for membership in data['memberships']:
            if membership.get("contact_details"):
                for x in membership['contact_details']:
                    cds.append(x)

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
    contact_details = set([x.id for x in person.contacts.all()])

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

        if cd.id in contact_details:
            contact_details.remove(cd.id)

    for id_ in (contact_details):
        # OK, We have a CD for an OCD person that we don't know about. Let's
        # blacklist this so that we don't send it. That would be bad news.
        detail = ContactDetail.objects.get(id=id_)
        print("I need to blacklist %s" % (str(detail)))
        detail.blacklist = True
        detail.save()
        # XXX: We should remove this if we've got no related things.
