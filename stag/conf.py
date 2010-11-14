import logging

logger = logging.getLogger('stagfs.conf')

class Settings(object):
    def __init__(self, configfile):
        pass

    def __getattr__(self, name):
        return getattr(self, "_"+name)()

    def _source_folders(self):
        return ('test_source',)

    def _db_name(self):
        return 'stagfs.sqlite'

    def _loaders(self):
        import loaders
        return (
            ('stag', loaders.StagfileLoader),
        )

    def _views(self):
        return ()

