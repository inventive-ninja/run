import os
import inspect
from pprint import pprint
from builtins import print
from collections import OrderedDict
from ..settings import settings
from ..task import Task, Module
from .error import ModuleAttributeError
from .metaclass import ModuleMetaclass
from .prototype import ModulePrototype


class Module(Task, Module, metaclass=ModuleMetaclass):

    # Public

    meta_prototype = ModulePrototype
    meta_convert = settings.convert
    meta_key = None
    meta_tags = []

    def __getattribute__(self, name):
        nested_name = None
        if '.' in name:
            # Nested name - split
            name, nested_name = name.split('.', 1)
        try:
            attribute = super().__getattribute__(name)
        except AttributeError as exception:
            # To get correct AttributeError message here
            if isinstance(exception, ModuleAttributeError):
                raise  # pragma: no cover TODO: remove
            raise ModuleAttributeError(
                'Module "{self}" has no attribute "{name}".'.
                format(self=self, name=name))
        if nested_name is not None:
            attribute = getattr(attribute, nested_name)
        return attribute

    def meta_lookup(self, name):
        nested_name = None
        if '.' in name:
            # Nested name - split
            name, nested_name = name.split('.', 1)
        # TODO: add good exception text here like in __getattribute__
        task = self.meta_tasks[name]
        if nested_name is not None:
            task = task.meta_lookup(nested_name)
        return task

    def meta_invoke(self, *args, **kwargs):
        default = getattr(self, self.meta_default)
        result = default(*args, **kwargs)
        return result

    @property
    def meta_basedir(self):
        if self.meta_is_main_module:
            file = inspect.getfile(type(self))
            basedir = os.path.abspath(os.path.dirname(file))
        else:
            basedir = self.meta_module.meta_basedir
        return self._meta_params.get('basedir', basedir)

    @meta_basedir.setter
    def meta_basedir(self, value):
        self._meta_params['basedir'] = value

    @property
    def meta_default(self):
        return self._meta_params.get('default', 'list')

    @meta_default.setter
    def meta_default(self, value):
        self._meta_params['default'] = value

    @property
    def meta_fullname(self):
        if self.meta_is_main_module:
            fullname = ''
            if self.meta_key is not None:
                fullname = '[{self.meta_key}]'.format(self=self)
            return fullname
        else:
            return super().meta_fullname

    @property
    def meta_is_main_module(self):
        """Module's main module status (is main module or not).
        """
        if self.meta_module:
            return False
        else:
            return True

    @property
    def meta_main_module(self):
        if self.meta_is_main_module:
            return self
        else:
            return super().meta_main_module

    @property
    def meta_style(self):
        return 'module'

    @property
    def meta_tasks(self):
        """Module's tasks dict-like object.

        Dict contains task instances, not values.
        """
        tasks = {}
        for name, attr in vars(type(self)).items():
            if isinstance(attr, Task):
                tasks[name] = attr
        return tasks

    # TODO: exception here caught in tests breaks system tests. Why?
    def list(self, task=None):
        """Print tasks.
        """
        if task is None:
            task = self
        else:
            task = self.meta_lookup(task)  # pragma: no cover TODO: remove
        names = []
        for name in sorted(dir(task)):
            # TODO: code duplication with ModuleMetaclass.__spawn__
            if name.isupper():
                continue  # pragma: no cover TODO: remove
            elif name.startswith('_'):
                continue
            elif name.startswith('meta_'):
                continue
            elif name in task.meta_tasks:
                nested_task = task.meta_tasks[name]
                name = nested_task.meta_format(mode='fullname')
            else:
                # TODO: code duplication with Task.meta_fullname
                separator = '.'
                if task.meta_is_main_module:
                    separator = ' '
                name = separator.join(filter(None,
                    [task.meta_fullname, name]))
            names.append(name)
        result = '\n'.join(names)
        print(result)

    def info(self, task=None):
        """Print information.
        """
        if task is None:
            task = self
        else:
            task = self.meta_lookup(task)
        info = task.meta_qualname
        info += task.meta_signature
        info += '\n---\n'
        info += 'Type: ' + task.meta_type
        info += '\n'
        info += 'Dependencies: ' + str(task.meta_dependencies)
        info += '\n'
        info += 'Default arguments: ' + str(task.meta_args)
        info += '\n'
        info += 'Default keyword arguments: ' + str(task.meta_kwargs)
        info += '\n---\n'
        info += task.meta_docstring
        print(info)

    def meta(self, task=None):
        """Print metadata.
        """
        if task is None:
            task = self
        else:
            task = self.meta_lookup(task)
        meta = OrderedDict()
        for name in sorted(dir(task)):
            if name.startswith('meta_'):
                key = name.replace('meta_', '')
                attr = getattr(task, name)
                if not inspect.ismethod(attr):
                    meta[key] = attr
        pprint(meta)
