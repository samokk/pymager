"""
    ImgServer RESTful Image Conversion Service 
    Copyright (C) 2008 Sami Dalouche

    This file is part of ImgServer.

    ImgServer is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ImgServer is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with ImgServer.  If not, see <http://www.gnu.org/licenses/>.

"""
import cherrypy
from imgserver.web.originalresource import OriginalResource
from imgserver.web.derivedresource import DerivedResource
from imgserver import config
from pkg_resources import resource_filename

class TopLevelResource(object):
    _cp_config = {
        'error_page.400': resource_filename('imgserver.web.templates', 'error-default.html'),
        'error_page.403': resource_filename('imgserver.web.templates', 'error-default.html'),
        'error_page.404': resource_filename('imgserver.web.templates', 'error-default.html'),
        'error_page.409': resource_filename('imgserver.web.templates', 'error-default.html')
    }
    def __init__(self, app_config, image_processor):
        self.__config = app_config
        self.__image_processor = image_processor
        self.original = OriginalResource(app_config, image_processor)
        self.derived = DerivedResource(app_config, image_processor)
    
    @cherrypy.expose
    def index(self):
        return "Top Level"