from .task import Task

class DerivedTask(Task):

    #Public
    
    def __init__(self, task, *args, **kwargs):
        self._task_name = task
        super().__init__(*args, **kwargs)

    def invoke(self, *args, **kwargs):
        return self._task(*args, **kwargs)

    @property
    def meta_docstring(self):
        return self._meta_params.get('docstring', 
            self._task.meta_docstring)         
     
    @property
    def meta_signature(self):
        return self._meta_params.get('signature', 
            self._task.meta_signature)        
    
    #Protected
    
    @property
    def _task(self):
        return getattr(self.meta_module, self._task_name)