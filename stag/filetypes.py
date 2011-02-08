
class StagFile(object):
    pass

class VirtualDirectory(StagFile):
    def __init__(self, contents):
        self._contents = contents

    def readdir(self):
        return self._contents

class RealFile(StagFile):
    def __init__(self, target):
        self._target = target

