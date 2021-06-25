"""
Basic building blocks for generic class based views.

We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""
from __future__ import unicode_literals

import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.utils.serdatajson import serdata2json
from rest_framework.signals import api_created, api_updated
import threading


class CreateModelMixin(object):
    """
    Create a model instance.
    """

    def create(self, request, *args, **kwargs):
        print("request", request.META.get('CONTENT_TYPE'))
        # request.data.pop("dataFile")
        # request.data.pop("reportFile")
        # rr = request.data.pop("reportFile")

        # print("rr",rr[0:100])
        print("requestdata", request.data)

        serializer = self.get_serializer(data=request.data)

        print("here")
        serializer.is_valid(raise_exception=True)
        print("here2")
        self.perform_create(serializer)
        print("here3")
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}


class ListModelMixin(object):
    """
    List a queryset.
    """

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RetrieveModelMixin(object):
    """
    Retrieve a model instance.
    """

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UpdateModelMixin(object):
    """
    Update a model instance.
    """

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        ser = serializer.__class__(instance)
        try:
            import threading
            import time
            from track_actions.requestMiddleware import RequestMiddleware

            current_request = RequestMiddleware.get_request_data()[1]
            class SaveHisThread(threading.Thread):
                def run(self):
                    print "start.... %s" % (self.getName(),)
                    old_data = serdata2json(ser.data)
                    print("dangqianuser",current_request.user)
                    api_updated.send(sender=serializer, current_request=current_request, old_data=old_data,
                                     new_data=request.data, instance=instance)
                    print "end.... %s" % (self.getName(),)

            savehistory = SaveHisThread()
            savehistory.start()

        except Exception as e:
            print(e)
            pass

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class DestroyModelMixin(object):
    """
    Destroy a model instance.
    """

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()
