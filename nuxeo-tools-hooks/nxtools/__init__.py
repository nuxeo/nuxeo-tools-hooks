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

    def add(self, service, name=None):
        if isinstance(service, type) or isinstance(service, ClassType):
            name = name if name else service.__module__ + "." + service.__name__
            if name not in [n for t, n, v in self.list(service)]:
                self.__raw.append((service, name, lambda: service()))
        else:
            name = name if name else service.__module__ + "." + type(service).__name__
            if name not in [n for t, n, v in self.list(type(service))]:
                self.__raw.append((type(service), name, lambda: service))

    def reload(self):
        del self.__values[:]

services = ServiceContainer()
