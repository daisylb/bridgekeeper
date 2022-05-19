from django import template

register = template.Library()


@register.simple_tag
def has_perm(perm, user, obj=None):
    if not hasattr(user, "has_perm"):
        return False  # swapped user model that doesn't support permissions
    else:
        return user.has_perm(perm, obj)
