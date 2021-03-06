from validator.decorator import version_range
from validator.constants import (FIREFOX_GUID, FENNEC_GUID,
                                 THUNDERBIRD_GUID as TB_GUID, ANDROID_GUID)


# Compatibility app/version ranges:

def _build_definition(maj_version_num, firefox=True, fennec=True,
                      thunderbird=True, android=True):
    definition = {}
    app_version_range = (
        lambda app: version_range(app, '%d.0a1' % maj_version_num,
                                       '%d.0a1' % (maj_version_num + 1)))
    if firefox:
        definition[FIREFOX_GUID] = app_version_range('firefox')
    if fennec:
        definition[FENNEC_GUID] = app_version_range('fennec')
    if thunderbird:
        definition[TB_GUID] = app_version_range('thunderbird')
    if android:
        definition[ANDROID_GUID] = app_version_range('android')

    return definition


FX45_DEFINITION = _build_definition(45)
FX46_DEFINITION = _build_definition(46)
FX47_DEFINITION = _build_definition(47)
FX48_DEFINITION = _build_definition(48)
