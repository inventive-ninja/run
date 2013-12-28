from run import Loader, settings

class LoadModule:

    #Public

    def __new__(self, names=[], tags=[],
                 path=settings.default_path,
                 file_pattern=settings.default_file, 
                 recursively=False):
        loader = Loader(names=names, tags=tags)
        for module_class in loader.load(path, file_pattern, recursively):
            module = module_class() 
            return module
        else:
            raise RuntimeError('No modules found')