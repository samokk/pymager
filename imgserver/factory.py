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
import os
from imgserver import imgengine, persistence
from imgserver.imgengine import image_transformation_security_decorator
from imgserver.imgengine.transformationrequest import TransformationRequest
from imgserver.imgengine.imagerequestprocessor import ImageRequestProcessor
from imgserver.imgengine.imagerequestprocessor import IImageRequestProcessor
from imgserver.persistence.schemamigrator import SchemaMigrator
from imgserver.persistence.sqlalchemyschemamigrator import SqlAlchemySchemaMigrator
from imgserver.domain.imagemetadatarepository import ImageMetadataRepository
from imgserver.persistence.sqlalchemyimagemetadatarepository import SqlAlchemyImageMetadataRepository

class ServiceConfiguration(object):
    def __init__(self, data_directory, dburi, allowed_sizes, dev_mode):
        self.data_directory = data_directory
        self.dburi = dburi
        self.allowed_sizes = allowed_sizes
        self.dev_mode = dev_mode

class ImageServerFactory(object):
    def __init__(self, config):
        super(ImageServerFactory, self)
        self.__schema_migrator = None
        self.__image_metadata_repository = None
        self.__image_processor = None
        self.__config = config

    def get_schema_migrator(self):
        return self.__schema_migrator


    def get_image_metadata_repository(self):
        return self.__image_metadata_repository


    def get_image_processor(self):
        return self.__image_processor

    def create_image_server(self):
        self.__schema_migrator = SchemaMigrator(SqlAlchemySchemaMigrator(self.__config.dburi))
        
        self.__image_metadata_repository = ImageMetadataRepository(SqlAlchemyImageMetadataRepository(self.__schema_migrator))
        self.__image_processor = IImageRequestProcessor(ImageRequestProcessor(self.__image_metadata_repository, self.__schema_migrator, self.__config.data_directory, self.__config.dev_mode))
        self.__image_processor.prepare_transformation =  image_transformation_security_decorator.image_transformation_security_decorator(self.__config.allowed_sizes)(self.__image_processor.prepare_transformation)
        
        return self.__image_processor
    
    schema_migrator = property(get_schema_migrator, None, None, "PersistenceProvider's Docstring")
    image_metadata_repository = property(get_image_metadata_repository, None, None, "ImageMetadataRepository's Docstring")
    image_processor = property(get_image_processor, None, None, "ImageProcessor's Docstring")
