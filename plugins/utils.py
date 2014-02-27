from django.template.loader import get_template
from django.template import Context


def body_template_to_string(template_set, module, attempt):
    """
    """
    path = "plugins/{set}/{module}.body".format(
        set=template_set,
        module=module
    )
    return _render_template_path(path, attempt)


def subject_template_to_string(template_set, module, attempt):
    """
    """
    path = "plugins/{set}/{module}.subject".format(
        set=template_set,
        module=module
    )
    return _render_template_path(path, attempt)


def intro_template_to_string(template_set, module, attempt):
    """
    """
    path = "plugins/{set}/{module}.intro".format(
        set=template_set,
        module=module
    )
    return _render_template_path(path, attempt)


def _render_template_path(path, attempt):
    return get_template(path).render(Context({
        "attempt": attempt,
        "person": attempt.contact.person,
        "contact": attempt.contact,
        "messages": attempt.messages.all(),
    }))
