import os
import sys
from jinja2 import Environment, FileSystemLoader, Template
from jinja2.utils import concat
from run import Task

class RenderTask(Task):
    
    #Public
    
    #TODO: adjust to new basedir!
    def __init__(self, source, target, **kwargs):
        self._source = source
        self._target = target
        
    def complete(self):
        dirname, filename = os.path.split(os.path.abspath(self._source))
        environment = Environment(loader=FileSystemLoader(dirname))
        environment.template_class = ModuleTemplate
        template = environment.get_template(filename)
        text = template.render(ModuleContext(self.meta_module))
        with open(self._target, 'w') as file:
            file.write(text)
            

class ModuleTemplate(Template):
    
    #Public
    
    def render(self, module_context):
        try:
            context = self.new_context(module_context, shared=True)
            return concat(self.root_render_func(context))
        except Exception:
            exc_info = sys.exc_info()
        return self.environment.handle_exception(exc_info, True)
        
        
class ModuleContext:
    
    #Public
    
    def __init__(self, module):
        self._module = module
        
    #TODO: hasattr?? (it hits Var.retrieve)
    def __contains__(self, key):
        return hasattr(self._module, key) 
        
    def __getitem__(self, key):
        try:
            return getattr(self._module, key)
        except AttributeError:
            raise KeyError(key)        