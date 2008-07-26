import shutil

from imgserver.factory import ImageServerFactory, ServiceConfiguration
from imgserver.web.cherrypyweb.toplevelresource import TopLevelResource

DB_FILENAME='db.sqlite'

def init_imageprocessor(config):    
    f = ImageServerFactory(config)
    imageProcessor = \
        f.createImageServer()
    #imageProcessor = \
    #    f.createImageServer(
    #        site_config.data_directory, 
    #        'postgres://imgserver:funala@localhost/imgserver',
    #        [(100,100), (800,600)], True)
    from pkg_resources import resource_filename
    if config.dev_mode:
        imageProcessor.saveFileToRepository(resource_filename('imgserver.samples', 'sami.jpg'),'sami')
    return imageProcessor

# allowed_sizes=[(100,100), (800,600)]
def create_site(config):
    config = ServiceConfiguration(
        data_directory=config['data_directory'] if (config.__contains__('data_directory')) else '/tmp/imgserver', 
        dburi=config['dburi'] if (config.__contains__('dburi')) else 'sqlite:////tmp/db.sqlite', 
        allowed_sizes=config['allowed_sizes'] if (config.__contains__('allowed_sizes')) else None,
        dev_mode= config['dev_mode'] if (config.__contains__('dev_mode')) else False)
    top_level_resource = \
        TopLevelResource(
            config, 
            init_imageprocessor(config))
    return top_level_resource 