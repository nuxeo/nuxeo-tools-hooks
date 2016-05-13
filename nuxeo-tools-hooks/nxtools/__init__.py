
class ServiceContainer(object):

    def __init__(self):
        self.__services = dict()

    @staticmethod
    def service(name=None):
        def decorator(f):
            services.add(f(), name)
            return f
        return decorator

    def get(self, clazz, name=None):
        for service_name in self.__services:
            service = self.__services[service_name]
            if clazz == type(service):
                if name:
                    if name == service_name:
                        return service
                else:
                    return service
        raise KeyError

    def add(self, service, name=None):
        name = name if name else type(service).__name__
        self.__services[name] = service

services = ServiceContainer()
