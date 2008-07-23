import shutil

from imgserver.factory import ImageServerFactory
from imgserver.web.cherrypyweb.toplevelresource import TopLevelResource

DB_FILENAME='db.sqlite'

class SiteConfig(object):
    def __init__(self, data_directory):
        self.data_directory = data_directory

def init_imageprocessor(site_config):
    shutil.rmtree(site_config.data_directory,True)
    f = ImageServerFactory()
    imageProcessor = \
        f.createImageServer(
            site_config.data_directory, 
            'sqlite:///%s/%s' % ('/tmp', DB_FILENAME),
            [(100,100), (800,600)],True)
    #imageProcessor = \
    #    f.createImageServer(
    #        site_config.data_directory, 
    #        'postgres://imgserver:funala@localhost/imgserver',
    #        [(100,100), (800,600)], True)
    from pkg_resources import resource_filename
    imageProcessor.saveFileToRepository(resource_filename('imgserver.samples', 'sami.jpg'),'sami')
    return imageProcessor

def create_site():
    site_config = SiteConfig('/tmp/imgserver')
    top_level_resource = \
        TopLevelResource(
            site_config, 
            init_imageprocessor(site_config))
    return top_level_resource 