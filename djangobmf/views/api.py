#!/usr/bin/python
# ex:set fileencoding=utf-8:

from __future__ import unicode_literals

from django.apps import apps
from django.http import Http404

from djangobmf.filters import ViewFilterBackend
from djangobmf.filters import RangeFilterBackend
from djangobmf.filters import RelatedFilterBackend
from djangobmf.pagination import ModulePagination
from djangobmf.views.mixins import BaseMixin

from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import CreateModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.mixins import DestroyModelMixin
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet


class APIMixin(BaseMixin):

    filter_backends = (ViewFilterBackend, RangeFilterBackend, RelatedFilterBackend)
    pagination_class = ModulePagination
    paginate_by = 100

    @property
    def model(self):
        if getattr(self, '_model', None):
            return self._model

        try:
            self._model = apps.get_model(self.kwargs.get('app'), self.kwargs.get('model'))
        except LookupError:
            raise Http404

        if not hasattr(self._model, '_bmfmeta'):
            raise Http404

        return self._model

    def get_queryset(self):
        qs = self.model._bmfmeta.filter_queryset(
            self.model.objects.all(),
            self.request.user,
        )
        return qs

    def get_serializer_class(self):
        """
        return the serializer which is registered with the model
        """
        return self.model._bmfmeta.serializer_class


class APIModuleOverView(BaseMixin, APIView):
    """
    All registered modules which are viewable by the current user
    """

    def get_view_name(self):
        return 'Modules'

    def get(self, request, format=None):
        """
        """
        site = request.djangobmf_site
        modules = []
        for ct, model in site.models.items():

            info = model._meta.app_label, model._meta.model_name
            perm = '%s.view_%s' % info
            if self.request.user.has_perms([perm]):  # pragma: no branch
                modules.append({
                    'name': model._meta.verbose_name_plural,
                    'url': reverse('djangobmf:api', request=request, format=format, kwargs={
                        'app': model._meta.app_label,
                        'model': model._meta.model_name,
                    }),
                    'only_related': model._bmfmeta.only_related,
                })
        return Response(modules)


class APIViewList(BaseMixin, APIView):
    """
    All registered Views which are viewable by the current user
    """

    def get_view_name(self):
        return 'Views'

    def get(self, request, format=None):
        """
        """
        dashboards = []

        for dashboard in self.request.djangobmf_site.dashboards:
            categories = []

            for category in dashboard:
                views = []

                for view in category:
                    # parse the function name
                    name = 'djangobmf:dashboard_%s:view_%s_%s' % (
                        dashboard.key,
                        category.key,
                        view.key,
                    )

                    # add the view if the user has the permissions to view it
                    if view().check_permissions(self.request):
                        views.append({
                            'name': view.name,
                            'key': view.key,
                            'url': reverse(name),
                            'api': reverse('djangobmf:api-view', request=request, format=format, kwargs={
                                'db': dashboard.key,
                                'cat': category.key,
                                'view': view.key,
                            }),
                        })

                if views:
                    categories.append({
                        'name': category.name,
                        'key': category.key,
                        'views': views,
                    })

            if categories:
                dashboards.append({
                    'name': dashboard.name,
                    'key': dashboard.key,
                    'categories': categories,
                })

        return Response(dashboards)


class APIViewDetail(BaseMixin, APIView):

    def get(self, request, view=None, cat=None, db=None, format=None):
        """
        """
        usernames = [1, 2, 3, 4, 5, 6, 7, 8]
        return Response(usernames)


class ViewSet(APIMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    pass


class APIModuleListView(APIMixin, ListModelMixin, CreateModelMixin, GenericAPIView):

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class APIModuleDetailView(APIMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView):

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
