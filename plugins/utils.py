from django.template.loader import get_template
from django.template import Context


def template_to_string(template_set, module, attempt):
    """
    """
    path = "plugins/{set}/{module}".format(
        set=template_set,
        module=module
    )
    return get_template(path).render(Context({"attempt": attempt}))
