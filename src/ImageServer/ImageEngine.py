import Image, ImageOps
import mimetypes
import os, os.path, shutil, time
from ImageServer import Domain, Persistence

# Relative to the data_directory
CACHE_DIRECTORY = "cache"
ORIGINAL_DIRECTORY = "pictures"
FORMAT_EXTENSIONS = { "JPEG" : "jpg" }

LOCK_MAX_RETRIES = 10
LOCK_WAIT_SECONDS = 1

# Layout
# data/original/image_id.format
# data/cache/image_id/800x600/format

def checkid(imageId):
    if not imageId.isalnum():
        raise IDNotAuthorized, imageId
            
class ImageProcessingException(Exception):
    """Thrown when errors happen while processing images """
    def __init__(self, message):
        super(ImageProcessingException, self).__init__(message)
        

class IDNotAuthorized(ImageProcessingException):
    def __init__(self, imageId):
        super(IDNotAuthorized, self).__init__('ID contains non alpha numeric characters: %s' % (imageId,))
        self.imageId = imageId

class ImageFileNotRecognized(ImageProcessingException):
    def __init__(self, ex):
        super(ImageFileNotRecognized, self).__init__(ex)

class ImageIDAlreadyExistingException(ImageProcessingException):
    def __init__(self, imageId):
        super(ImageIDAlreadyExistingException, self).__init__('An image with the given ID already exists in the repository: %s' % imageId)
        self.imageId = imageId


class TransformationRequest(object):
    """ Stores the parameters of an image processing request """
    def __init__(self, imageId, size, target_format):
        """ @param size: a (width, height) tuple
        """
        checkid(imageId)
        
        self.imageId = imageId
        self.size = size
        self.targetFormat = target_format

class ImageRequestProcessor(object):
    
    """ Processes ImageRequest objects and does the required work to prepare the images """
    def __init__(self, itemRepository, dataDirectory):
        """ @param data_directory: the directory that this 
            ImageRequestProcessor will use for its work files """
        self.__dataDirectory = dataDirectory 
        self.__initDirectories()
        self.__itemRepository = itemRepository
        
    def __initDirectories(self):
        """ Creates the work directories needed to run this processor """
        for directory in \
            [self.__absoluteCacheDirectory(), self.__absoluteOriginalDirectory()]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
    def __absoluteCacheDirectory(self):
        """ @return: the directory that will be used for caching image processing 
        results """
        return os.path.join(self.__dataDirectory, CACHE_DIRECTORY)
    
    def __absoluteOriginalDirectory(self):
        """ @return. the directory that will be used to store original files, 
        before processing"""
        return os.path.join (self.__dataDirectory, ORIGINAL_DIRECTORY)
    
    def __absoluteOriginalFilename(self, originalItem):
        """ returns the filename of the original file """
        return os.path.join (self.__absoluteOriginalDirectory(), '%s.%s' % (originalItem.id, self.__extensionForFormat(originalItem.format)))
    
    def __absoluteCachedFilename(self, derivedItem):
        
        return os.path.join( self.__dataDirectory,
                            self.__relativeCachedFilename(derivedItem))
    
    def __relativeCachedFilename(self, derivedItem):
        """ relative to the base directory """
        return os.path.join ( CACHE_DIRECTORY, 
                              '%s-%sx%s.%s' % (derivedItem.originalItem.id, derivedItem.size[0], derivedItem.size[1],self.__extensionForFormat(derivedItem.format)))
        
    def __extensionForFormat(self, format):
        return FORMAT_EXTENSIONS[format.upper()] if FORMAT_EXTENSIONS.__contains__(format.upper()) else format.lower()

    def saveFileToRepository(self, filename, imageId):
        """ save the given file to the image server repository. 
        It will then be available for transformations"""
        
        checkid(imageId)
        # Check that the image is not broken
        try:
            img = Image.open(filename)
            img.verify()
        except IOError, ex:
            raise ImageFileNotRecognized, ex
        
        item = Domain.OriginalItem(imageId, Domain.STATUS_INCONSISTENT, img.size, img.format)

        try:
            # atomic creation
            self.__itemRepository.create(item)
        except Persistence.DuplicateEntryException, ex:
            raise ImageIDAlreadyExistingException, item.id
        else:
            try:
                shutil.copyfile(filename, self.__absoluteOriginalFilename(item))
            except IOError, ex:
                raise ImageProcessingException, ex
        
        item.status = Domain.STATUS_OK
        self.__itemRepository.update(item)
        
    
    def __waitForItemStatusOk(self, pollingCallback):
        """ Wait for the status property of the object returned by pollingCallback() to be STATUS_OK
        It honors LOCK_MAX_RETRIES and LOCK_WAIT_SECONDS
        """
        item = pollingCallback()
        i = 0
        while i < LOCK_MAX_RETRIES and item is not None and item.status != Domain.STATUS_OK:
            time.sleep(LOCK_WAIT_SECONDS)
            item = pollingCallback()
            i=i+1
        
    def prepareTransformation(self, transformationRequest):
        """ Takes an ImageRequest and prepare the output for it. 
            Updates the database so that it is in sync with the filesystem
            @return: the path to the generated file (relative to the cache directory) 
            """
        originalItem = self.__itemRepository.findOriginalItemById(transformationRequest.imageId)
        assert originalItem is not None
        
        self.__waitForItemStatusOk(lambda: self.__itemRepository.findOriginalItemById(transformationRequest.imageId))
        
        derivedItem = Domain.DerivedItem(Domain.STATUS_INCONSISTENT, transformationRequest.size, transformationRequest.targetFormat, originalItem)
        
        cached_filename = self.__absoluteCachedFilename(derivedItem)
        relative_cached_filename = self.__relativeCachedFilename(derivedItem)

        # if image is already cached...
        if os.path.exists(cached_filename):
            return relative_cached_filename
        
        # otherwise, c'est parti to convert the stuff
        try:
            self.__itemRepository.create(derivedItem)
            original_filename = self.__absoluteOriginalFilename(originalItem)
        except Persistence.DuplicateEntryException :
            self.__waitForItemStatusOk(lambda: self.__itemRepository.findDerivedItemByOriginalItemIdSizeAndFormat(originalItem.id, transformationRequest.size, transformationRequest.targetFormat)) 
            
        try:
            img = Image.open(original_filename)
        except IOError, ex: 
            raise ImageProcessingException, ex
        
        if transformationRequest.size == img.size and transformationRequest.target_format.upper() == img.format.upper():
            try:
                shutil.copyfile(self.__absoluteOriginalFilename(originalItem), cached_filename)
            except IOError, ex:
                raise ImageProcessingException, ex
        else:   
            target_image = ImageOps.fit(image=img, 
                                        size=transformationRequest.size, 
                                        method=Image.ANTIALIAS,
                                        centering=(0.5,0.5)) 
            try:
                target_image.save(cached_filename)
            except IOError, ex:
                raise ImageProcessingException, ex
        
        derivedItem.status = Domain.STATUS_OK
        self.__itemRepository.update(derivedItem)
        
        return relative_cached_filename
    
    def cleanupInconsistentItems(self):
        pass

