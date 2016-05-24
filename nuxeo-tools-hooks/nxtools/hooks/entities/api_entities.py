
class ViewObjectWrapper(object):
    def __init__(self, *args):
        self.__wrappees = list(args)

    def __getattr__(self, attr):
        for wrappee in self.__wrappees:
            try:
                return getattr(wrappee, attr)
            except AttributeError:
                pass

        raise AttributeError
