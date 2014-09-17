import os
import inspect
from copy import copy
from abc import abstractmethod
from box.collections import merge_dicts
from box.terminal import Formatter
from box.types import Null
from contextlib import contextmanager
from ..converter import Result
from ..dependency import Predecessor, Successor, require, trigger
from ..settings import settings
from .error import TaskInheritError
from .metaclass import TaskMetaclass
from .signal import TaskSignal


class Task(Result, Predecessor, Successor, metaclass=TaskMetaclass):

    # Public

    @classmethod
    def __meta_create__(cls, *args, meta_module, meta_updates, **kwargs):
        # Create task object
        self = object.__new__(cls)
        # Initiate module, updates
        self.__meta_module = meta_module
        self.__meta_updates = meta_updates
        # Initiate params
        self.__meta_params = {}
        for key in list(kwargs):
            if key.startswith('meta_'):
                name = key.replace('meta_', '')
                self.__meta_params[name] = kwargs.pop(key)
        # Initiate directory
        self.__meta_initial_dir = os.path.abspath(os.getcwd())
        # Initiate cache
        self.__meta_cached_result = Null
        # Initiate dependencies
        self.__meta_dependencies = []
        self.__init_dependencies()
        # Initiate arguments
        self.__meta_args = ()
        self.__meta_kwargs = {}
        # Call user init
        self.__init__(*args, **kwargs)
        return self

    def __meta_update__(self):
        for update in self.__meta_updates:
            update.apply(self)

    def __init__(self, *args, **kwargs):
        self.__meta_args = args
        self.__meta_kwargs = kwargs

    def __get__(self, module, module_class=None):
        if self.meta_is_descriptor:
            if self.meta_cache:
                if self.__meta_cached_result is Null:
                    self.__meta_cached_result = self()
                return self.__meta_cached_result
            else:
                return self()
        return self

    def __call__(self, *args, **kwargs):
        self.__add_signal('called')
        try:
            self.__resolve_dependencies()
            try:
                eargs = self.meta_args + args
                ekwargs = merge_dicts(self.meta_kwargs, kwargs)
                with self.__change_directory():
                    result = self.meta_invoke(*eargs, **ekwargs)
            except Exception:
                if self.meta_fallback is not None:
                    result = self.meta_fallback
                else:
                    self.__resolve_dependencies(failed=True)
                    raise
            self.__resolve_dependencies(failed=False)
        except Exception:
            self.__add_signal('failed')
            raise
        self.__add_signal('successed')
        return result

    def __repr__(self):
        pattern = '<{self.meta_type}>'
        if self.meta_qualname:
            pattern = '<{self.meta_type} "{self.meta_qualname}">'
        return pattern.format(self=self)

    def meta_format(self, mode='name'):
        result = str(getattr(self, 'meta_' + mode, ''))
        if result:
            if not self.meta_plain:
                style = settings.styles.get(self.meta_style, None)
                if style is not None:
                    formater = Formatter()
                    result = formater.format(result, **style)
        return result

    def meta_depend(self, dependency):
        """Add custom dependency.
        """
        dependency.bind(self)
        self.meta_dependencies.append(dependency)

    # TODO: rename?
    def meta_not_depend(self, task):
        """Remove all of task dependencies.
        """
        task = self.meta_module.meta_lookup(task)
        for dependency in copy(self.meta_dependencies):
            if dependency.predecessor is task:
                self.meta_dependencies.remove(dependency)

    def meta_require(self, task, *args, **kwargs):
        """Add require dependency.
        """
        dependency = require(task, *args, **kwargs)
        self.meta_depend(dependency)

    def meta_trigger(self, task, *args, **kwargs):
        """Add trigger dependency.
        """
        dependency = trigger(task, *args, **kwargs)
        self.meta_depend(dependency)

    @abstractmethod
    def meta_invoke(self, *args, **kwargs):
        """Invoke task.
        """
        pass  # pragma: no cover

    # TODO: rename?
    def meta_getmeta(self, name, *, inherit=False, default=Null):
        fullname = 'meta_' + name
        try:
            return self.__meta_params[name]
        except KeyError:
            if inherit:
                try:
                    return self.meta_derive(fullname)
                except TaskInheritError:
                    pass
        if default is not Null:
            return default
        raise AttributeError(fullname)

    # TODO: rename?
    def meta_setmeta(self, name, value):
        self.__meta_params[name] = value

    # TODO: rename?
    def meta_derive(self, name):
        if self.meta_module is None:
            raise TaskInheritError(name)
        # TODO: add inheritance check
        return getattr(self.meta_module, name)

    @property
    def meta_args(self):
        """Tasks's default arguments
        """
        return self.__meta_args

    @property
    def meta_basedir(self):
        """Task's basedir.

        If meta_chdir is True current directory will be
        changed to meta_basedir when task invoking.

        This property is:

        - initable/writable
        - inherited from module
        """
        return self.meta_getmeta(
            'basedir', inherit=True, default=os.path.abspath(os.getcwd()))

    @meta_basedir.setter
    def meta_basedir(self, value):
        self.meta_setmeta('basedir', value)

    @property
    def meta_cache(self):
        """Task's caching status (enabled or disabled).

        If meta_cache is True descriptor tasks cache result of invocations.

        This property is:

        - initable/writable
        - inherited from module
        """
        return self.meta_getmeta(
            'cache', inherit=True, default=settings.cache)

    @meta_cache.setter
    def meta_cache(self, value):
        self.meta_setmeta('cache', value)

    @property
    def meta_chdir(self):
        """Task's chdir status (enabled or disabled).

        .. seealso:: :attr:`run.Task.meta_basedir`

        This property is:

        - initable/writable
        - inherited from module
        """
        return self.meta_getmeta(
            'chdir', inherit=True, default=settings.chdir)

    @meta_chdir.setter
    def meta_chdir(self, value):
        self.meta_setmeta('chdir', value)

    @property
    def meta_dependencies(self):
        """Task's list of dependencies.
        """
        return self.__meta_dependencies

    @property
    def meta_dispatcher(self):
        """Task's dispatcher.

        Dispatcher used to operate signals.

        This property is:

        - initable/writable
        - inherited from module
        """
        return self.meta_getmeta(
            'dispatcher', inherit=True, default=None)

    @meta_dispatcher.setter
    def meta_dispatcher(self, value):
        self.meta_setmeta('dispatcher', value)

    @property
    def meta_docstring(self):
        """Task's docstring.

        This property is:

        - initable/writable
        """
        return self.meta_getmeta(
            'docstring', default=str(inspect.getdoc(self)).strip())

    @meta_docstring.setter
    def meta_docstring(self, value):
        self.meta_setmeta('docstring', value)

    @property
    def meta_fallback(self):
        """Task's fallback.

        Fallback used when task invocation fails.

        This property is:

        - initable/writable
        - inherited from module
        """
        return self.meta_getmeta(
            'fallback', inherit=True, default=settings.fallback)

    @meta_fallback.setter
    def meta_fallback(self, value):
        self.meta_setmeta('fallback', value)

    @property
    def meta_fullname(self):
        fullname = ''
        if self.meta_module:
            separator = '.'
            if self.meta_module.meta_is_main_module:
                separator = ' '
            fullname = separator.join(filter(None,
                [self.meta_module.meta_fullname, self.meta_name]))
        return fullname

    @property
    def meta_is_descriptor(self):
        return False

    @property
    def meta_kwargs(self):
        """Tasks's default keyword arguments
        """
        return self.__meta_kwargs

    # TODO: move only to Module? Remove?
    @property
    def meta_main_module(self):
        """Task's main module of module hierarchy.
        """
        main_module = None
        if self.meta_module:
            main_module = self.meta_module.meta_main_module
        return main_module

    @property
    def meta_module(self):
        """Task's module.
        """
        return self.__meta_module

    @property
    def meta_name(self):
        """Task's name.

        Name is defined as task name in module.
        """
        name = ''
        if self.meta_module:
            tasks = self.meta_module.meta_tasks
            for key, task in tasks.items():
                if task is self:
                    name = key
        return name

    @property
    def meta_qualname(self):
        """Task's qualified name.

        Qualname is full task name in hierarhy starts
        from main module.
        """
        qualname = ''
        if self.meta_module:
            module_qualname = self.meta_module.meta_qualname
            qualname = '.'.join(filter(None, [module_qualname, self.meta_name]))
        return qualname

    @property
    def meta_plain(self):
        """Task's plain flag (plain or not).

        This property is:

        - initable/writable
        - inherited from module
        """
        return self.meta_getmeta(
            'plain', inherit=True, default=settings.plain)

    @meta_plain.setter
    def meta_plain(self, value):
        self.meta_setmeta('plain', value)

    @property
    def meta_signature(self):
        """Task's signature.

        This property is:

        - initable/writable
        """
        return self.meta_getmeta(
            'signature', default=str(inspect.signature(self.meta_invoke)))

    @meta_signature.setter
    def meta_signature(self, value):
        self.meta_setmeta('signature', value)

    @property
    def meta_strict(self):
        """Task's strict mode status (enabled or disabled).

        This property is:

        - initable/writable
        - inherited from module
        """
        return self.meta_getmeta(
            'strict', inherit=True, default=settings.strict)

    @meta_strict.setter
    def meta_strict(self, value):
        self.meta_setmeta('strict', value)

    @property
    def meta_style(self):
        return 'task'

    @property
    def meta_type(self):
        """Task's type as a string.
        """
        return type(self).__name__

    # Protected

    def __init_dependencies(self):
        for dependency in self.__meta_params.get('depend', []):
            self.meta_depend(dependency)
        for task in self.__meta_params.get('require', []):
            self.meta_require(task)
        for task in self.__meta_params.get('trigger', []):
            self.meta_trigger(task)

    def __add_signal(self, event):
        if self.meta_dispatcher:
            signal = TaskSignal(self, event=event)
            self.meta_dispatcher.add_signal(signal)

    def __resolve_dependencies(self, failed=None):
        for dependency in self.meta_dependencies:
            dependency.resolve(failed=failed)

    @contextmanager
    def __change_directory(self):
        if self.meta_chdir:
            previous_dir = os.path.abspath(os.getcwd())
            following_dir = os.path.join(
                self.__meta_initial_dir, self.meta_basedir)
            os.chdir(following_dir)
            yield
            os.chdir(previous_dir)
        else:
            yield
