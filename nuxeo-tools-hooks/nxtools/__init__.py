"""
(C) Copyright 2016 Nuxeo SA (http://nuxeo.com/) and contributors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
you may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Contributors:
    Pierre-Gildas MILLON <pgmillon@nuxeo.com>
"""
from types import ClassType


class ServiceContainer(object):

    @staticmethod
    def service(clazz, name=None):
        services.add(clazz, name)
        return clazz

    def __init__(self):
        self.__raw = []
        self.__values = []

    def get(self, clazz, name=None):
        if name:
            return [raw_value for raw_type, raw_name, raw_value in self.list(clazz) if raw_name == name][0]
        else:
            return [raw_value for raw_type, raw_name, raw_value in self.list(clazz)][0]

    def list(self, clazz):
        self.__values.extend([(raw_type, raw_name, raw_value()) for raw_type, raw_name, raw_value in self.__raw
                              if issubclass(raw_type, clazz) and
                              (raw_type, raw_name) not in [(t, n) for t, n, v in self.__values]])

        return [(raw_type, raw_name, raw_value) for raw_type, raw_name, raw_value in self.__values
                if issubclass(raw_type, clazz)]

    def add(self, service, name=None, replace=False):
        is_type = isinstance(service, type) or isinstance(service, ClassType)
        found = False

        if is_type:
            raw_name = name if name else service.__module__ + "." + service.__name__
            raw_type = service
            service_collection = self.__raw
        else:
            raw_name = name if name else service.__module__ + "." + type(service).__name__
            raw_type = type(service)
            service_collection = self.__values

        for index, existing_service in enumerate(service_collection):
            existing_type, existing_name, existing_value = existing_service
            if raw_name == existing_name:
                if replace:
                    del service_collection[index]
                else:
                    found = True

        if not found:
            if is_type:
                self.__raw.append((raw_type, raw_name, lambda: service()))
            else:
                self.__values.append((raw_type, raw_name, service))

    def reload(self):
        del self.__values[:]

services = ServiceContainer()
