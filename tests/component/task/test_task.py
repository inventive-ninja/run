import os
import unittest
from functools import partial
from importlib import import_module
from unittest.mock import Mock, call, patch
component = import_module('run.task.task')


class TaskTest(unittest.TestCase):

    # Actions

    def setUp(self):
        self.module = Mock()
        self.update = Mock()
        self.args = ('arg1',)
        self.kwargs = {'kwarg1': 'kwarg1'}
        self.Task = self.make_task_class()
        self.pTask = partial(
            self.Task, meta_module=None, meta_updates=[self.update])
        self.task = self.pTask(*self.args, **self.kwargs)

    # Helpers

    def make_task_class(self):
        class Task(component.Task):
            """docstring"""
            # Public
            meta_invoke = Mock(return_value='value')
        return Task

    # Tests

    def test(self):
        # Check update.apply call
        self.update.apply.assert_called_with(self.task)

    def test___get__(self):
        self.assertEqual(self.task.__get__('module'), self.task)

    def test___get___with_meta_is_descriptor(self):
        self.Task.meta_is_descriptor = True
        self.Task.meta_cache = False
        self.assertEqual(self.task.__get__('module'), 'value')
        self.assertEqual(self.task.__get__('module'), 'value')
        # Two calls because of caching is off
        self.assertEqual(self.task.meta_invoke.call_count, 2)

    @patch.object(component, 'TaskSignal')
    def test___get___with_meta_is_descriptor_and_meta_cache(self, TaskSignal):
        self.Task.meta_is_descriptor = True
        self.Task.meta_cache = True
        self.Task.meta_dispatcher = Mock()
        self.assertEqual(self.task.__get__('module'), 'value')
        self.assertEqual(self.task.__get__('module'), 'value')
        # Only one call because of caching
        self.assertEqual(self.task.meta_invoke.call_count, 1)
        self.task.meta_invoke.assert_called_with(*self.args, **self.kwargs)
        # Check TaskSignal call
        TaskSignal.assert_has_calls(
            [call(self.task, event='called'),
             call(self.task, event='successed')])
        # Check dispatcher.add_signal call
        self.task.meta_dispatcher.add_signal.assert_has_calls(
            [call(TaskSignal.return_value),
             call(TaskSignal.return_value)])

    @patch.object(component, 'TaskSignal')
    def test___call__(self, TaskSignal):
        self.Task.meta_dispatcher = Mock()
        self.assertEqual(self.task(), 'value')
        # Check meta_invoke call
        self.task.meta_invoke.assert_called_with(*self.args, **self.kwargs)
        # Check TaskSignal call
        TaskSignal.assert_has_calls(
            [call(self.task, event='called'),
             call(self.task, event='successed')])
        # Check dispatcher.add_signal call
        self.task.meta_dispatcher.add_signal.assert_has_calls(
            [call(TaskSignal.return_value),
             call(TaskSignal.return_value)])

    @patch.object(component, 'TaskSignal')
    def test___call___with_meta_invoke_exception(self, TaskSignal):
        self.Task.meta_dispatcher = Mock()
        self.Task.meta_invoke.side_effect = Exception()
        self.assertRaises(Exception, self.task)
        # Check TaskSignal call
        TaskSignal.assert_has_calls(
            [call(self.task, event='called'),
             call(self.task, event='failed')])
        # Check dispatcher.add_signal call
        self.task.meta_dispatcher.add_signal.assert_has_calls(
            [call(TaskSignal.return_value),
             call(TaskSignal.return_value)])

    def test___call___with_meta_invoke_exception_and_meta_fallback(self):
        self.Task.meta_invoke.side_effect = Exception()
        self.Task.meta_fallback = 'fallback'
        self.assertEqual(self.task(), 'fallback')

    def test___call___with_dependencies(self):
        dependency = Mock()
        self.task.meta_depend(dependency)
        self.assertEqual(self.task(), 'value')
        # Check dependnecy resolve call
        dependency.resolve.assert_has_calls([
            call(failed=None),
            call(failed=False)])

    def test___call___with_dependencies_and_meta_invoke_exception(self):
        dependency = Mock()
        self.task.meta_depend(dependency)
        self.task.meta_invoke.side_effect = Exception()
        self.assertRaises(Exception, self.task)
        # Check dependnecy resolve call
        dependency.resolve.assert_has_calls([
            call(failed=None),
            call(failed=True)])

    def test___call___with_meta_chdir_is_false(self):
        self.Task.meta_chdir = False
        self.assertEqual(self.task(), 'value')

    def test___repr__(self):
        self.assertEqual(repr(self.task), '<Task>')

    def test___repr___with_meta_module(self):
        self.Task.meta_module = self.module
        self.module.meta_qualname = 'module'
        self.module.meta_tasks = {'task': self.task}
        self.assertEqual(repr(self.task), '<Task "module.task">')

    def test_meta_format(self):
        self.Task._styles = {'task': {'foreground': 'bright_green'}}
        self.assertEqual(self.task.meta_format(attribute='meta_type'),
                         '\x1b[92mTask\x1b[m')

    def test_meta_format_with_meta_plain_is_true(self):
        self.Task.meta_plain = True
        self.Task._styles = {'task': {'foreground': 'bright_green'}}
        self.assertEqual(self.task.meta_format(attribute='meta_type'), 'Task')

    def test_meta_depend(self):
        dependency = Mock()
        self.task.meta_depend(dependency)
        self.assertEqual(self.task.meta_dependencies, [dependency])
        # Check dependency's bind call
        dependency.bind.assert_called_with(self.task)

    def test_meta_not_depend(self):
        dependency1 = Mock()
        dependency1.predecessor = 'task1'
        dependency2 = Mock()
        dependency2.predecessor = 'task2'
        self.module.meta_lookup.return_value = 'task1'
        self.Task.meta_dependencies = [dependency1, dependency2]
        self.task = self.Task(meta_module=self.module)
        self.task.meta_not_depend('task1')
        self.assertEqual(self.task.meta_dependencies, [dependency2])

    @patch.object(component, 'require')
    def test_meta_require(self, require):
        self.task.meta_require('task', *self.args, **self.kwargs)
        self.assertEqual(self.task.meta_dependencies, [require.return_value])
        # Check require call
        require.assert_called_with('task', *self.args, **self.kwargs)
        # Check require's return_value (require dependency) bind call
        require.return_value.bind.assert_called_with(self.task)

    @patch.object(component, 'trigger')
    def test_meta_trigger(self, trigger):
        self.task.meta_trigger('task', *self.args, **self.kwargs)
        self.assertEqual(self.task.meta_dependencies, [trigger.return_value])
        # Check trigger call
        trigger.assert_called_with('task', *self.args, **self.kwargs)
        # Check trigger's return_value (trigger dependency) bind call
        trigger.return_value.bind.assert_called_with(self.task)

    def test_meta_args(self):
        self.assertEqual(self.task.meta_args, self.args)

    def test_meta_basedir(self):
        self.assertEqual(self.task.meta_basedir,
                         os.path.abspath(os.getcwd()))

    def test_meta_cache(self):
        self.assertEqual(self.task.meta_cache, component.settings.cache)

    def test_meta_chdir(self):
        self.assertEqual(self.task.meta_chdir, component.settings.chdir)

    def test_meta_dependencies(self):
        self.assertEqual(self.task.meta_dependencies, [])

    @patch.object(component, 'trigger')
    @patch.object(component, 'require')
    def test_meta_dependencies_initter(self, require, trigger):
        dependency = Mock()
        self.task = self.pTask(
            meta_depend=[dependency],
            meta_require=['require'],
            meta_trigger=['trigger'])
        self.assertEqual(
            self.task.meta_dependencies,
            [dependency,
             require.return_value,
             trigger.return_value])
        # Check require, trigger call
        require.assert_called_with('require')
        trigger.assert_called_with('trigger')
        # Check dependency's bind call
        dependency.bind.assert_called_with(self.task)
        require.return_value.bind.assert_called_with(self.task)
        trigger.return_value.bind.assert_called_with(self.task)

    @unittest.skip
    def test_meta_dispatcher(self):
        self.assertEqual(self.task.meta_dispatcher, None)

    def test_meta_docstring(self):
        self.assertEqual(self.task.meta_docstring,
                         self.task.__doc__)

    def test_meta_fallback(self):
        self.assertEqual(self.task.meta_fallback, component.settings.fallback)

    def test_meta_fullname(self):
        self.assertEqual(self.task.meta_fullname, '')

    def test_meta_fullname_with_meta_module(self):
        self.Task.meta_module = self.module
        self.module.meta_fullname = 'module'
        self.module.meta_is_main_module = False
        self.module.meta_tasks = {'task': self.task}
        self.assertEqual(self.task.meta_fullname, 'module.task')

    def test_meta_fullname_with_meta_module_is_main(self):
        self.Task.meta_module = self.module
        self.module.meta_fullname = '[key]'
        self.module.meta_is_main_module = True
        self.module.meta_tasks = {'task': self.task}
        self.assertEqual(self.task.meta_fullname, '[key] task')

    def test_meta_is_descriptor(self):
        self.assertEqual(self.task.meta_is_descriptor, False)

    def test_meta_kwargs(self):
        self.assertEqual(self.task.meta_kwargs, self.kwargs)

    def test_meta_main_module(self):
        self.assertIsNone(self.task.meta_main_module)

    def test_meta_main_module_with_meta_module(self):
        self.Task.meta_main_module = self.module
        self.assertEqual(self.task.meta_main_module, self.module)

    def test_meta_module(self):
        self.assertIsNone(self.task.meta_module)

    def test_meta_module_with_meta_module(self):
        self.task = self.Task(meta_module=self.module)
        self.assertEqual(self.task.meta_module, self.module)

    def test_meta_name(self):
        self.assertEqual(self.task.meta_name, '')

    def test_meta_name_with_meta_module(self):
        self.Task.meta_module = self.module
        self.module.meta_tasks = {'task': self.task}
        self.assertEqual(self.task.meta_name, 'task')

    def test_meta_qualname(self):
        self.assertEqual(self.task.meta_qualname, '')

    def test_meta_qualname_with_meta_module(self):
        self.Task.meta_module = self.module
        self.module.meta_qualname = 'module'
        self.module.meta_tasks = {'task': self.task}
        self.assertEqual(self.task.meta_qualname, 'module.task')

    def test_meta_plain(self):
        self.assertEqual(self.task.meta_plain, component.settings.plain)

    def test_meta_signature(self):
        self.assertEqual(self.task.meta_signature, '(*args, **kwargs)')

    def test_meta_strict(self):
        self.assertEqual(self.task.meta_strict, component.settings.strict)

    def test_meta_style(self):
        self.assertEqual(self.task.meta_style, 'task')

    def test_meta_type(self):
        self.assertEqual(self.task.meta_type, 'Task')
