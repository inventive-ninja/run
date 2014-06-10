from tests.system.test_examples import ExamplesTest

class IntroductionTest(ExamplesTest):
    
    #Public        
    
    __test__ = True
    
    def test_greet(self):
        result = self._execute('greet', messages=['Hi'])
        self.assertEqual(
            result, 
            'Type your greeting (Hello): '
            'We\'re ready to say Hi to person.\n'
            'Hi World 3 times!\n'
            'We\'re done.\n')
        
    #Protected 
        
    @property
    def _file(self):
        return 'introduction.py'
