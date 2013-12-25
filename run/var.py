import inspect
from abc import ABCMeta, abstractmethod
from .dependent import DependentAttribute

class Var(DependentAttribute, metaclass=ABCMeta):
    
    #Public

    def __get__(self, module, module_class=None):
        self._resolve_requirements()
        #TODO: add error handling   
        result = self.retrieve()
        self._process_triggers()
        #TODO: reimplement!
        print('Retrieved: '+self.meta_name)
        #print('Retrieved '+str(self))             
        return result
 
    @abstractmethod
    def retrieve(self):
        pass #pragma: no cover
    
    
class ValueVar(Var):
    
    #Public
    
    def __init__(self, value):
        self._value = value
 
    def retrieve(self):
        return self._value
    
    
class PropertyVar(Var):
    
    #Public
    
    def __init__(self, prop):
        self._property = prop
 
    def retrieve(self):
        return self._property.__get__(
            self.meta_module, self.meta_module.__class__)
    
    @property    
    def meta_docstring(self):
        return str(inspect.getdoc(self._property))          