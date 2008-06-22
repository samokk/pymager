from ImageServer import Domain
import sqlalchemy
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapper, relation, sessionmaker, scoped_session, eagerload
from sqlalchemy.sql import select
import os, logging


class DuplicateEntryException(Exception):
    """Thrown when errors happen while processing images """
    def __init__(self, duplicateId):
        self.__duplicateId = duplicateId
        Exception.__init__(self, 'Duplicated ID: %s' % duplicateId)

    def getDuplicateId(self):
        return self.__duplicateId
    
    duplicateId = property(getDuplicateId, None, None, "The ID that lead to the DuplicateEntryException")

class NoUpgradeScriptError(Exception):
    """Thrown when no upgrade script is found for a given schema_version """
    def __init__(self, schema_version):
        self.__schema_version = schema_version
        Exception.__init__(self, 'No upgrade script is found for Schema Version: %s' % schema_version)

    def getSchemaVersion(self):
        return self.__schema_version
    
    schemaVersion = property(getSchemaVersion, None, None, "The ID that lead to the DuplicateEntryException")

class Version(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class ItemRepository(object):
    """ DDD repository for Original and Derived Items """
    def __init__(self, persistenceProvider):
        self.__persistenceProvider = persistenceProvider
    
    def findOriginalItemById(self, item_id):
        """ Find an OriginalItem by its ID """
        def callback(session):
            return session.query(Domain.OriginalItem)\
                .filter(Domain.OriginalItem.id==item_id)\
                .first()
        return self.__persistenceProvider.do_with_session(callback)

    def findInconsistentOriginalItems(self, maxResults=100):
        """ Find Original Items that are in an inconsistent state """
        def callback(session):
            # FIXME: uncomment when inheritance bug is solved
            # return session.query(Domain.OriginalItem).filter(Domain.AbstractItem.status!='STATUS_OK').limit(maxResults).all()
            return session.query(Domain.OriginalItem)\
                .filter(Domain.OriginalItem.status!='STATUS_OK')\
                .limit(maxResults).all()
            #return session.query(Domain.OriginalItem).all()
        return self.__persistenceProvider.do_with_session(callback)    
    
    def findDerivedItemByOriginalItemIdSizeAndFormat(self, item_id, size, format):
        """ Find Derived Items By :
            - the Original Item ID
            - the size of the Derived Item
            - the format of the Derived Item """
        def callback(session):
            return session.query(Domain.DerivedItem)\
                    .filter_by(width=size[0])\
                    .filter_by(height=size[1])\
                    .filter_by(format=format)\
                    .join('originalItem')\
                    .filter_by(id=item_id)\
                    .first()
        return self.__persistenceProvider.do_with_session(callback)
    
    def create(self, item):
        """ Create a persistent instance of an item"""
        def callback(session):
            session.save(item)
        try:
            self.__persistenceProvider.do_with_session(callback)
        except sqlalchemy.exceptions.IntegrityError, ex: 
            raise DuplicateEntryException, item.id
    
    def update(self, item):
        """ Create a persistent instance, or update an existing item 
            @raise DuplicateEntryException: when an item with similar characteristics has already been created  
        """
        def callback(session):
            session.save_or_update(item)
        try:
            self.__persistenceProvider.do_with_session(callback)
        except sqlalchemy.exceptions.IntegrityError: 
            raise DuplicateEntryException, item.id
    


class PersistenceProvider(object):
    """ Manages the Schema, Metadata, and stores references to the Engine and Session Maker """
    def __init__(self, dbstring):
        self.__engine = create_engine(dbstring, encoding='utf-8', echo=False)
        self.__metadata = MetaData()
        self.__sessionmaker = sessionmaker(bind=self.__engine, autoflush=True, transactional=True)
        
        version = Table('version', self.__metadata,
            Column('name', String(255), primary_key=True),
            Column('value', Integer)
        )
        
        # FIXME: inheritance bug...
        #abstract_item = Table('abstract_item', self.__metadata,
        #    Column('id', String(255), primary_key=True),
        #    Column('status', String(255), index=True, nullable=False),
        #    Column('width', Integer, index=True, nullable=False),
        #    Column('height', Integer, index=True, nullable=False),
        #    Column('format', String(255), index=True, nullable=False),
        #    Column('type', String(255), nullable=False)
        #)
        
        original_item = Table('original_item', self.__metadata,
            Column('id', String(255), primary_key=True),
            Column('status', String(255), index=True, nullable=False),
            Column('width', Integer, index=True, nullable=False),
            Column('height', Integer, index=True, nullable=False),
            Column('format', String(255), index=True, nullable=False)  
            #Column('id', String(255), ForeignKey('abstract_item.id'), primary_key=True),
            #Column('info', String(255)),
        )
        
        derived_item = Table('derived_item', self.__metadata,
            Column('id', String(255), primary_key=True),
            Column('status', String(255), index=True, nullable=False),
            Column('width', Integer, index=True, nullable=False),
            Column('height', Integer, index=True, nullable=False),
            Column('format', String(255), index=True, nullable=False),
            #Column('id', String(255), ForeignKey('abstract_item.id'), primary_key=True),
            Column('original_item_id', String(255), ForeignKey('original_item.id', ondelete="CASCADE")),
            UniqueConstraint('original_item_id', 'height', 'width', 'format')
        )

        #mapper(Domain.AbstractItem, abstract_item, polymorphic_on=abstract_item.c.type, polymorphic_identity='ABSTRACT_ITEM') 
        mapper(Domain.OriginalItem, original_item) #, inherits=Domain.AbstractItem, polymorphic_identity='ORIGINAL_ITEM'
        mapper(Domain.DerivedItem, derived_item, 
               properties={ 
                           'originalItem' : relation(Domain.OriginalItem, primaryjoin=derived_item.c.original_item_id==original_item.c.id, lazy=False)
                           }) #, inherits=Domain.AbstractItem , polymorphic_identity='DERIVED_ITEM'
        mapper(Version, version)
    
    def do_with_session(self, session_callback):
        session = self.__sessionmaker()
        o = session_callback(session)
        session.commit()
        session.close()
        return o
    
    def createOrUpgradeSchema(self):
        """ Create or Upgrade the database metadata
        @raise NoUpgradeScriptError: when no upgrade script is found for a given 
            database schema version
         """
        def get_version(session):
            schema_version = None
            try:
                schema_version = session.query(Version)\
                                    .filter(Version.name=='schema')\
                                    .first()
                schema_version = schema_version if schema_version is not None else Version('schema', 0)
            except sqlalchemy.exceptions.OperationalError:
                schema_version = Version('schema', 0) 
            return schema_version
        
        def store_latest_version(session):
            version = get_version(session)
            version.value = 1
            session.save_or_update(version)
            
        schema_version = self.do_with_session(get_version)
        if schema_version.value == 0:
            self.__metadata.create_all(self.__engine)
            self.do_with_session(store_latest_version)
        elif schema_version == 1:
            # nothing to do, already the latest version 
            pass
        else:
            raise NoUpgradeScriptError(schema_version)
