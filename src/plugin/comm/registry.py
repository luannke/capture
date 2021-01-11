# coding: utf-8

__all__ = ["Registry", "plug", "func"]


class Registry:
    """
    the registry that provides name obj mapping
    used as a decorator to store class and method name
    in order to establish instance according class name, incoming parameters
    (in init build-in, get web content, auto run method that marked to parse data)
    finally return data property(in fact, it's a Metadata instance)
    """
    _plugins = {}
    _funcs = {}

    @classmethod
    def class_deco(cls, _obj):
        """
        decorator, store plugin classes into a dict
        name as key, obj as value
        Args:
            _obj (class):

        """
        cls._plugins[_obj.__name__] = _obj
        return _obj

    @classmethod
    def func_deco(cls, _func):
        """
        does not really change the behavior of the decorated function
        also simply add attribute works
        decorator, store func, autorun later
        Attention: __qualname__ get class and method name
        eg. Javbus.info
        Args:
            _func (function):

        """
        cls._funcs[_func.__qualname__] = _func
        return _func

    @classmethod
    def _register(cls, service_id: str, number, config):
        """
        get obj from plugin dict
        Args:
            service_id (str): obj name

        Returns: obj instance

        """
        service = cls._plugins.get(service_id)
        if service is None:
            raise KeyError(
                "No object named '{}' found in plugins!".format(service)
            )
        return service(number, config)

    @classmethod
    def get(cls, service_id: str, number, config):
        """
        get instance and run all decorated instance method
        Args:
            config ():
            number ():
            service_id ():

        Returns: instance data

        """
        obj = cls._register(service_id, number, config)
        if obj is not None:
            map(exec, [f(obj) for i, f in cls._funcs.items() if service_id in i])
            return obj.data

    def __repr__(self) -> list:
        return [i for i, j in self._plugins.items()]

    def __contains__(self, name: str) -> bool:
        return name in self._plugins

    def __iter__(self):
        return iter(self._plugins.items())

    @classmethod
    def check_data(cls, service_id, number, config):
        """
        an interface that only acquires data
        Args:
            config ():
            service_id ():
            number ():
        """
        data = cls.get(service_id, number, config)
        for key, value in data.items():
            print(f'{key}: {value}')
        # return data

    __str__ = __repr__


plug = Registry().class_deco
func = Registry().func_deco
