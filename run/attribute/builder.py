from copy import copy

class AttributeBuilder:
    
    #Public
    
    def __init__(self, cls, *args, **kwargs):
        self._module = kwargs.pop('module', None)
        self._updates = kwargs.pop('updates', [])
        self._class = cls
        self._args = list(args)
        self._kwargs = kwargs
        
    def __copy__(self):
        return self.fork()
     
    def build(self, *args, **kwargs):
        """Make object using forked builder with args, kwargs"""
        builder = self.fork(*args, **kwargs)
        obj = builder.make()
        return obj
            
    def fork(self, *args, **kwargs):
        """Fork builder with applied args, kwargs"""
        eargs = self._args+list(args)
        ekwargs = copy(self._kwargs)
        ekwargs.update(kwargs)
        ekwargs.setdefault('module', self._module)
        ekwargs.setdefault('updates', copy(self._updates))
        builder = type(self)(self._class, *eargs, **ekwargs)
        return builder
    
    def make(self):
        """Make object for this builder"""
        obj = self._create_object()
        self._init_object(obj)
        return obj     
    
    @property
    def cls(self):
        return self._class
    
    @property
    def args(self):
        return self._args
    
    @property
    def kwargs(self):
        return self._kwargs
    
    @property
    def module(self):
        return self._module
    
    @property
    def updates(self):
        return self._updates
    
    #Protected
             
    def _create_object(self):
        return object.__new__(self._class)
        
    def _init_object(self, obj):
        obj.__meta_build__(self)
        if self._module != True:
            obj.__meta_init__(self._module)
    
    
def build(attribute, *args, **kwargs):
    return attribute.meta_builder.build(*args, **kwargs)