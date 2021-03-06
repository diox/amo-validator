from call_definitions import open_in_chrome_context
from instanceproperties import _set_HTML_property
from validator.compat import FX47_DEFINITION, FX48_DEFINITION
from validator.constants import BUGZILLA_BUG, MDN_DOC


ENTITIES = {}


def register_entity(name):
    """Allow an entity's modifier to be registered for use."""
    def wrap(func):
        ENTITIES[name] = func
        return func
    return wrap


def entity(name, result=None):
    assert name in ENTITIES

    def return_wrap(t):
        output = ENTITIES[name](traverser=t)
        if result is not None:
            return result
        elif output is not None:
            return output
        else:
            return {'value': {}}
    return {'value': return_wrap}


def deprecated_entity(name, version, message, bug, status='deprecated',
                      compat_type='error'):
    def wrap(traverser):
        traverser.err.warning(
            err_id=('js', 'entities', name),
            warning='`%s` has been %s.' % (name, status),
            description=(message,
                         'See %s for more information.' % BUGZILLA_BUG % bug),
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context,
            for_appversions=version,
            compatibility_type=compat_type,
            tier=5)
    register_entity(name)(wrap)

def register_changed_entities(version_definition, entities, version_string):
    for entity in entities:
        deprecated_entity(
            name=entity['name'],
            version=version_definition,
            message='The method or property `%s` has been `%s` in `%s`.'
                % (entity['name'], entity['status'], version_string),
            bug=entity['bug'],
            compat_type=entity['compat_type'])


DOC_WRITE_MSG = ('https://developer.mozilla.org/docs/XUL/School_tutorial/'
                 'DOM_Building_and_HTML_Insertion')

@register_entity('document.write')
def document_write(traverser):
    def on_write(wrapper, arguments, traverser):
        traverser.err.warning(
            err_id=('js', 'document.write', 'evil'),
            warning='Use of `document.write` strongly discouraged.',
            description=('`document.write` will fail in many circumstances ',
                         'when used in extensions, and has potentially severe '
                         'security repercussions when used improperly. '
                         'Therefore, it should not be used. See %s for more '
                         'information.' % DOC_WRITE_MSG),
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)
        if not arguments:
            return
        value = traverser._traverse_node(arguments[0])
        _set_HTML_property('document.write()', value, traverser)

    return {'return': on_write}


@register_entity('nsIDNSService.resolve')
def nsIDNSServiceResolve(traverser):
    traverser.err.warning(
        err_id=('testcases_javascript_entity_values',
                'nsIDNSServiceResolve'),
        warning='`nsIDNSService.resolve()` should not be used.',
        description='The `nsIDNSService.resolve` method performs a '
                    'synchronous DNS lookup, which will freeze the UI. This '
                    'can result in severe performance issues. '
                    '`nsIDNSService.asyncResolve()` should be used instead.',
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context)


@register_entity('nsISound.play')
def nsISoundPlay(traverser):
    traverser.err.warning(
        err_id=('testcases_javascript_entity_values',
                'nsISound_play'),
        warning='`nsISound.play` should not be used.',
        description='The `nsISound.play` function is synchronous, and thus '
                    'freezes the interface while the sound is playing. It '
                    'should be avoided in favor of the HTML5 audio APIs.',
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context)


@register_entity('nsIWindowWatcher.openWindow')
def nsIWindowWatcher_openWindow(traverser):
    def on_open(wrapper, arguments, traverser):
        if not arguments:
            return
        uri = traverser._traverse_node(arguments[0])
        open_in_chrome_context(uri, 'nsIWindowWatcher.openWindow', traverser)

    return {'return': on_open}


@register_entity('nsITransferable.init')
def nsITransferable_init(traverser):
    def on_init(wrapper, arguments, traverser):
        if not arguments:
            return
        first_arg = traverser._traverse_node(arguments[0])
        if first_arg.get_literal_value():
            return
        traverser.err.warning(
            err_id=('js_entity_values', 'nsITransferable', 'init'),
            warning='`init` should not be called with a null first argument',
            description='Calling `nsITransferable.init()` with a null first '
                        'argument has the potential to leak data across '
                        'private browsing mode sessions. `null` is  '
                        'appropriate only when reading data or writing data '
                        'which is not associated with a particular window.',
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)

    return {'return': on_init}


@register_entity('NewTabURL.override')
def NewTabURL_override(traverser):
    def on_override(wrapper, arguments, traverser):
        # Import loop.
        from validator.testcases.javascript.predefinedentities import (
            CUSTOMIZATION_API_HELP)
        traverser.err.warning(
            err_id=('js_entity_values', 'NewTabURL', 'override'),
            warning='Extensions must not alter user preferences such as the '
                    'new tab URL without explicit user consent.',
            description='Extensions must not alter user preferences such as '
                        'the new tab URL without explicit user consent. Such '
                        'changes must also be reverted when the extension is '
                        'disabled or uninstalled.',
            signing_severity='high',
            signing_help='Add-ons which directly change these preferences must '
                         'undergo manual code review for at least one '
                         'submission. ' + CUSTOMIZATION_API_HELP,
        )
    return {'return': on_override}


@register_entity('nsIObserverService.addObserver')
def nsIObserverService_addObserver(traverser):
    def on_addObserver(wrapper, arguments, traverser):
        if not arguments:
            return

        first_arg = traverser._traverse_node(arguments[1]).get_literal_value()

        if first_arg == 'newtab-url-changed':
            traverser.err.warning(
                err_id=('js_entity_values', 'nsIObserverService', 'newtab_url_changed'),
                warning='Extensions must not use the `newtab-url-changed` event to '
                        'revert changes made to the new tab url.',
                description='To avoid conflicts, extensions are not allowed to '
                            'add an observer to the `newtab-url-changed` event '
                            'in order to revert changes that have been made to '
                            'the new tab url.',
                signing_severity='high',
                signing_help='Add-ons which use `newtab-url-changed` to change '
                             'the new tab url are not allowed.')

    # Return the addObserver handler and a general dangerous warning.
    return {
        'return': on_addObserver,
        'dangerous': lambda a, t, e:
            e.get_resource('em:bootstrap') and
            'Authors of bootstrapped add-ons must take care '
            'to remove any added observers '
            'at shutdown.'
    }


@register_entity('nsIPK11TokenDB.listTokens')
@register_entity('nsIPKCS11ModuleDB.listModules')
@register_entity('nsIPKCS11Module.listSlots')
def nsIPK11TokenDB(traverser):
    traverser.err.warning(
        err_id=('testcases_javascript_entity_values',
                'nsIPKThings'),
        warning='listTokens(), listModules() and listSlots() now return '
                'nsISimpleEnumerator instead of nsIEnumerator.',
        description=(
            'listTokens(), listModules() and listSlots() now return '
            'nsISimpleEnumerator instead of nsIEnumerator.'
            'See %s for more information.' % BUGZILLA_BUG % 1220237),
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        for_appversions=FX47_DEFINITION,
        compatibility_type='error',
        context=traverser.context,
        tier=5)


@register_entity('nsIIOService.newChannel')
@register_entity('nsIIOService.newChannelFromURI')
@register_entity('nsIIOService.newChannelFromURIWithProxyFlags')
def nsIIOService(traverser):
    traverser.err.warning(
        err_id=('testcases_javascript_entity_values',
                'nsIIOService'),
        warning=(
            'The "newChannel" functions have been deprecated in favor of '
            'their new versions (ending with 2).'),
        description=(
            'The "newChannel" functions have been deprecated in favor of '
            'their new versions (ending with 2). '
            'See %s for more information.'
            % MDN_DOC % 'Mozilla/Tech/XPCOM/Reference/Interface/nsIIOService'),
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        for_appversions=FX48_DEFINITION,
        compatibility_type='warning',
        context=traverser.context,
        tier=5)
