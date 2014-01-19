import unittest
from functools import partial
from unittest.mock import Mock, call
from run.run.run import Run

class RunTest(unittest.TestCase):

    #Public
    
    def setUp(self):
        MockRun = self._make_mock_run_class()
        self.partial_run = partial(MockRun,
            names='names', 
            tags='tags', 
            filename='filename', 
            basedir='basedir',
            recursively='recursively',
            existent='existent', 
            stackless='dispatcher')
        
    def test_run(self):
        run = self.partial_run()
        args = ('arg1',)
        kwargs = {'kwarg1': 'kwarg1',}
        run.run('attribute', *args, **kwargs)
        for attr in run._cluster_class.return_value.attribute:
            if hasattr(attr, 'assert_called_with'):
                attr.assert_called_with(*args, **kwargs)
        run._print_operator.assert_has_calls([
            call('result1'), 
            call('result2'),
            call('attr3')])
    
    def test__controller(self):
        run = self.partial_run()
        run._controller
        run._controller_class.assert_called_with(
            run._dispatcher, stackless=run._stackless)
        
    def test__dispatcher(self):
        run = self.partial_run()
        run._dispatcher
        run._dispatcher_class.assert_called_with()
        
    def test__cluster(self):
        run = self.partial_run()
        run._cluster
        run._cluster_class.assert_called_with(
            names='names', 
            tags='tags', 
            filename='filename', 
            basedir='basedir',
            recursively='recursively',
            existent='existent', 
            dispatcher=run._dispatcher_class.return_value)
        
    def test__filename_default(self):
        run = self.partial_run(filename=None)
        self.assertEqual(run._filename, 'default_filename')  
        
    def test__basedir_default(self):
        run = self.partial_run(basedir=None)
        self.assertEqual(run._basedir, 'default_basedir')
    
    #Protected
    
    def _make_mock_run_class(self):
        class MockRun(Run):
            #Protected
            _print_operator = Mock()
            _task_class = Mock
            _controller_class = Mock()
            _dispatcher_class = Mock(return_value=Mock(add_handler=Mock()))
            _cluster_class = Mock(return_value=Mock(attribute = [
                Mock(return_value='result1'), 
                Mock(return_value='result2'),
                'attr3']))
            _default_filename = 'default_filename'
            _default_basedir = 'default_basedir'
        return MockRun