# -*- coding: utf-8 -*-

from zope.component import queryUtility
from Products.CMFCore.utils import getToolByName

from plone.registry.interfaces import IRegistry
from Products.CMFPlone.utils import safe_unicode

from collective.analyticspanel import logger

from collective.analyticspanel.interfaces import IAnalyticsSettings, IAnalyticsSettingsSchema

PROFILE_ID = 'profile-collective.analyticspanel:default'

def setupVarious(context):
    if context.readDataFile('collective.analyticspanel_various.txt') is None:
        return

    portal = context.getSite()
    
    ptool = portal.portal_properties
    registry = queryUtility(IRegistry)
    settings = registry.forInterface(IAnalyticsSettingsSchema, check=False)

    if settings.general_code:
        logger.info('Already found a local analytics code in my registry: no operation taken')
        return

    plone_snippet = ptool.site_properties.webstats_js
    
    if plone_snippet:
        logger.info('Found a general analytics code: copying it in my registry')
        settings.general_code = safe_unicode(ptool.site_properties.webstats_js)


def migrateTo1001(context):
    registry = queryUtility(IRegistry)
    settings = registry.forInterface(IAnalyticsSettings, check=False)
    for path_config in settings.path_specific_code:
        if not hasattr(path_config, 'apply_to_subsection'):
            path_config.apply_to_subsection = True
            logger.info('Added new boolean property "apply_to_subsection" to %s' % safe_unicode(path_config.path))
    logger.info('Migrated to version 0.2')

def migrateTo1020(context):
    setup_tool = getToolByName(context, 'portal_setup')
    setup_tool.runImportStepFromProfile(PROFILE_ID, 'plone.app.registry')

    registry = queryUtility(IRegistry)
    old_settings = registry.forInterface(IAnalyticsSettings, check=False)
    new_settings = registry.forInterface(IAnalyticsSettingsSchema, check=False)
    if old_settings.general_code and not new_settings.general_code:
        new_settings.general_code = old_settings.general_code
        logger.info('Migrating general_code')
    if not new_settings.error_specific_code:
        for error_config in old_settings.error_specific_code:
            new_settings.error_specific_code += (error_config,)
            logger.info('Migrating an error_specific_code record for code %s' % error_config.message)
    if not new_settings.path_specific_code:
        for path_config in old_settings.path_specific_code:
            apply_to_subsection = path_config.apply_to_subsection
            del path_config.apply_to_subsection
            if apply_to_subsection:
                path_config.apply_to = u'subtree'
            else:
                path_config.apply_to = u'context'
            new_settings.path_specific_code += (path_config,)
            logger.info('Migrating a path_specific_code record for path %s' % path_config.path)
    setup_tool.runAllImportStepsFromProfile('profile-collective.analyticspanel:registry_cleanup')
    logger.info('Registry cleanup operation performed')
    logger.info('Migrated to version 0.3')
