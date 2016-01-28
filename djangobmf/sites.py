#!/usr/bin/python
# ex:set fileencoding=utf-8:

from __future__ import unicode_literals

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
# from django.db.models import Model

from djangobmf.conf import settings
from djangobmf.core import Relationship
from djangobmf.core.category import Category
from djangobmf.core.dashboard import Dashboard
from djangobmf.core.module import Module
from djangobmf.core.report import Report
from djangobmf.core.viewmixin import ViewMixin
from djangobmf.views.module import DetailView

import logging
logger = logging.getLogger(__name__)


__all__ = [
    'Category',
    'Dashboard',
    'Module',
    'Report',
    'ViewMixin',
]


# shortcut to the site instance to provide a simple
# syntax to add the framework to external modules
# please note, that this is only available, when the
# apps are loaded (cause the site does some database
# queries). Importing this to early leads to an exception
# which is a feature and not a bug.
if apps.apps_ready:  # pragma: no branch
    bmfappconfig = apps.get_app_config(settings.APP_LABEL)
    site = apps.get_app_config(settings.APP_LABEL).site

    class register(object):  # noqa
        def __init__(self, cls=None, **kwargs):
            self.kwargs = kwargs
            if cls:
                self.register_generic(cls)

        def __call__(self, cls):
            self.register_generic(cls)

        def register_category(self, category):
            dashboard = self.register_dashboard(category.dashboard)
            category = dashboard.add_category(category)
            return category

        def register_dashboard(self, dashboard):
            for db in site.dashboards:
                if isinstance(db, dashboard):
                    return db

            # Register and initialize the Dashboard
            db = dashboard(site)
            site.dashboards.append(db)
            logger.debug('Registered Dashboard "%s"', dashboard.__name__)
            return db

        def register_generic(self, cls):
            if issubclass(cls, ViewMixin):
                if "category" not in self.kwargs:
                    raise ImproperlyConfigured(
                        'You need to define a category, when registering the view %s',
                        cls,
                    )
                category = self.register_category(self.kwargs["category"])
                category.add_view(cls)
                logger.debug('Registered View "%s" to %s', cls.__name__, category.__class__.__name__)

            elif issubclass(cls, Relationship):
                if "model" not in self.kwargs:
                    raise ImproperlyConfigured(
                        'You need to define a module when registering the view %s',
                        cls.__name__,
                    )
                bmfappconfig.bmfregister_relationship(cls, self.kwargs["model"])

            elif issubclass(cls, Module):
                instance = bmfappconfig.bmfregister_module(cls)
                site.modules[cls.model] = instance

            elif issubclass(cls, Report):
                if "dashboard" not in self.kwargs:
                    raise ImproperlyConfigured(
                        'You need to define a dashbord, when registering the report %s',
                        cls,
                    )
                dashboard = self.register_dashboard(self.kwargs["dashboard"])
                dashboard.add_report(cls)

            elif issubclass(cls, DetailView):
                # TODO
                pass

            else:
                raise ImproperlyConfigured(
                    'You can not register %s with django-bmf',
                    cls,
                )

    __all__ += [
        'register',
        'site',
    ]
