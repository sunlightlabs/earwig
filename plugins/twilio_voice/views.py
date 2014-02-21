from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from ..base.twilio import validate

from ..utils import (intro_template_to_string, body_template_to_string,
                     subject_template_to_string)

from contact.models import DeliveryStatus, FeedbackType
from .models import TwilioVoiceStatus


def get_translate_contact(func):
    def get_translate_contact(request, contact_id, *args, **kwargs):
        status = TwilioVoiceStatus.objects.get(attempt__id=contact_id)
        return func(request, status, *args, **kwargs)
    return get_translate_contact


def _redirect_to_endpoint(request, base, url):
    return render(request, 'common/twilio/voice/redirect.xml',
                  {"url": "%s%s" % (base, url)},
                  content_type="application/xml")


@csrf_exempt
@validate
@get_translate_contact
def intro(request, status):
    attempt = status.attempt

    digits = request.POST.get("Digits", None)
    if digits:
        try:
            handler = lambda *args: _redirect_to_endpoint(request,
                                                          "../../", *args)
            return handler({
                "1": "messages/%s/" % (attempt.id),
                "9": "flag/%s/" % (attempt.id),
            }[digits])
        except KeyError:
            # Random keypress.
            pass

    man_or_machine = request.POST.get("AnsweredBy", "machine")

    template = attempt.template
    attempt.mark_attempted(DeliveryStatus.sent,
                           'twilio_voice', attempt.template)
    attempt.save()

    human_intro = intro_template_to_string(attempt.template,
                                           'voice.landing.human',
                                           attempt)

    machine_intro = intro_template_to_string(attempt.template,
                                             'voice.landing.human',
                                             attempt)
    is_machine = man_or_machine == "machine"
    if is_machine:
        print("Got a machine")
    else:
        print("Got a person")

    return render(request,
                  'common/twilio/voice/intro.xml',
                  {"attempt": attempt,
                   "status": status,
                   "person": attempt.contact.person,
                   "is_machine": is_machine,
                   "human_intro": human_intro,
                   "machine_intro": machine_intro,
                   "intro": (machine_intro if is_machine else human_intro),
                  },
                 content_type="application/xml")


@csrf_exempt
@validate
@get_translate_contact
def messages(request, status):
    attempt = status.attempt
    template = attempt.template
    return render(request,
                  'common/twilio/voice/messages.xml',
                  {"attempt": attempt,
                   "intro": intro_template_to_string(attempt.template,
                                                     'voice.landing',
                                                     attempt)},
                 content_type="application/xml")


@csrf_exempt
@validate
@get_translate_contact
def message(request, status, sequence_id):
    digits = request.POST.get("Digits", None)

    attempt = status.attempt
    template = attempt.template
    sequence_id = int(sequence_id)

    messages = list(attempt.messages.order_by('id'))
    message = messages[sequence_id].message
    sender = message.sender
    has_next = len(messages) > (sequence_id + 1)

    # 1 => next
    # 3 => respond
    # 0 => main menu
    digits = request.POST.get("Digits", None)
    if digits:
        try:
            handler = lambda *args: _redirect_to_endpoint(request,
                                                         "../../../", *args)
            return handler({
                "1": (
                    "message/%s/%s/" % (attempt.id, (sequence_id + 1))
                ) if has_next else ("intro/%s/" % (attempt.id)),
                # 1 is next until it's end of thread, when it becomes
                #
                "0": "intro/%s/" % (attempt.id),
            }[digits])
        except KeyError:
            # Random keypress.
            pass

    return render(request,
                  'common/twilio/voice/message.xml',
                  {"attempt": attempt,
                   "has_next": has_next,
                   "sender": sender,
                   "message": message},
                 content_type="application/xml")

@csrf_exempt
@validate
@get_translate_contact
def flag(request, status):
    attempt = status.attempt
    attempt.set_feedback(
        FeedbackType.wrong_person,
        "Flagged via the Phone Menu for review.",
    )
    attempt.save()

    return render(request,
                  'common/twilio/voice/flag.xml',
                  {"attempt": attempt,
                   "status": status,},
                 content_type="application/xml")
