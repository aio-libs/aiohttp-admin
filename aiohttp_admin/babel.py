def gettext(string, **variables):
    return string % variables


def ngettext(singular, plural, num, **variables):
    variables.setdefault('num', num)
    return (singular if num == 1 else plural) % variables


def lazy_gettext(string, **variables):
    return gettext(string, **variables)


class Translations(object):
    """dummy Translations class for WTForms, no translation support"""
    def gettext(self, string):
        return gettext(string)

    def ngettext(self, singular, plural, n):
        return ngettext(singular, plural, n)
