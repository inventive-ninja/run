import os
import re
import sys
import inspect
import importlib
from lib31.python import cachedproperty
from packgram.console import Program, Command
from .sub import Sub
from .settings import settings

class Program(Program):
    
    #Public
        
    def __call__(self):
        for sub in self._subs:
            sub.make() 
            
    #Protected
        
    @cachedproperty
    def _command(self):
        return Command(self.argv, schema=settings.command_schema)
    
    @cachedproperty
    def _subs(self):
        subs = []
        dirname, filename = os.path.split(os.path.abspath(self._command.file))
        self._switch_to_directory(dirname)
        modulename = re.sub('\.pyc?', '', filename)
        #TODO: add no module handling
        module = importlib.import_module(modulename)
        for filename in dir(module):
            attr = getattr(module, filename)
            if (isinstance(attr, type) and
                not inspect.isabstract(attr) and
                issubclass(attr, Sub)):
                subs.append(attr())
        return subs
        
    def _switch_to_directory(self, dirname):
        os.chdir(dirname)
        sys.path.insert(0, dirname) 
    
           
program = Program(sys.argv)           