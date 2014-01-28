from django.core.management.base import BaseCommand, CommandError
from contact.models import (ContactPlugin,)
import json
import os


class Command(BaseCommand):
    args = '<load_plugins file>'
    help = 'Load the plugins into the DB'

    def handle(self, path, **kwargs):
        with open(os.path.abspath(path), 'r') as fd:
            data = json.load(fd)
        for obj in data:
            p = ContactPlugin(**obj)
            p.save()
