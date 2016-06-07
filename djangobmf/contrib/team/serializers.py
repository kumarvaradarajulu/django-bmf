#!/usr/bin/python
# ex:set fileencoding=utf-8:

from __future__ import unicode_literals

from djangobmf.serializers import ModuleSerializer


class TeamSerializer(ModuleSerializer):
    class Meta:
        fields = (
            'name',
            'members',
        )
