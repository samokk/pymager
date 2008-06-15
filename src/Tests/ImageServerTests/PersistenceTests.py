import unittest
from ImageServer import Domain, Persistence
from Tests import Support

class PersistenceTestCase(Support.AbstractIntegrationTestCase):
    
    def onSetUp(self):
        self.itemRepository = self.imageServerFactory.getItemRepository() 
    
    def testShouldNotFindAnyItemWhenIdDoesNotExist(self):
        assert self.itemRepository.findOriginalItemById('anyId') is None
    
    def testShouldSaveAndFindOriginalItem(self):
        item = Domain.OriginalItem('MYID12435', Domain.STATUS_OK, (800, 600), 'JPEG')
        self.itemRepository.create(item)
        foundItem = self.itemRepository.findOriginalItemById('MYID12435')
        assert foundItem is not None
        assert foundItem.id == 'MYID12435'
        assert foundItem.status == Domain.STATUS_OK
        assert foundItem.width == 800
        assert foundItem.height == 600
        assert foundItem.format == 'JPEG'

    def testShouldNotFindAnyOriginalItem(self):
        foundItem = self.itemRepository.findOriginalItemById('MYID12435')
        assert foundItem is None
        
    def testShouldSaveAndFindDerivedItemByOriginalItemIdAndSize(self):
        originalItem = Domain.OriginalItem('MYID12435', Domain.STATUS_OK, (800, 600), 'JPEG')
        self.itemRepository.create(originalItem)
        
        item = Domain.DerivedItem(Domain.STATUS_OK, (100, 100), 'JPEG', originalItem)
        self.itemRepository.create(item)
        foundItem = self.itemRepository.findDerivedItemByOriginalItemIdAndSize('MYID12435', (100,100))
        assert foundItem is not None
        assert foundItem.status == Domain.STATUS_OK
        assert foundItem.width == 100
        assert foundItem.height == 100
        assert foundItem.format == 'JPEG'
        assert foundItem.originalItem.id == 'MYID12435'
        assert foundItem.originalItem.status == Domain.STATUS_OK
        assert foundItem.originalItem.width == 800
        assert foundItem.originalItem.height == 600
        assert foundItem.originalItem.format == 'JPEG'
    
    def testShouldNotFindAnyDerivedItemIfWidthDoesNotMatch(self):
        originalItem = Domain.OriginalItem('MYID12435', Domain.STATUS_OK, (800, 600), 'JPEG')
        self.itemRepository.create(originalItem)
        
        item = Domain.DerivedItem(Domain.STATUS_OK, (100, 100), 'JPEG', originalItem)
        self.itemRepository.create(item)
        foundItem = self.itemRepository.findDerivedItemByOriginalItemIdAndSize('MYID12435', (101,100))
        assert foundItem is None
        
    def testShouldNotFindAnyDerivedItemIfHeightDoesNotMatch(self):
        originalItem = Domain.OriginalItem('MYID12435', Domain.STATUS_OK, (800, 600), 'JPEG')
        self.itemRepository.create(originalItem)
        
        item = Domain.DerivedItem(Domain.STATUS_OK, (100, 100), 'JPEG', originalItem)
        self.itemRepository.create(item)
        foundItem = self.itemRepository.findDerivedItemByOriginalItemIdAndSize('MYID12435', (100,101))
        assert foundItem is None
    
    def testShouldNotFindAnyDerivedItemIfIdDoesNotMatch(self):
        originalItem = Domain.OriginalItem('MYID12435', Domain.STATUS_OK, (800, 600), 'JPEG')
        self.itemRepository.create(originalItem)
        
        item = Domain.DerivedItem(Domain.STATUS_OK, (100, 100), 'JPEG', originalItem)
        self.itemRepository.create(item)
        foundItem = self.itemRepository.findDerivedItemByOriginalItemIdAndSize('ANOTHERID', (100,100))
        assert foundItem is None
    
    def testSaveTwoOriginalItemsWithSameIDShouldThrowException(self):
        item = Domain.OriginalItem('MYID12435', Domain.STATUS_OK, (800, 600), 'JPEG')
        item2 = Domain.OriginalItem('MYID12435', Domain.STATUS_INCONSISTENT, (700, 100), 'JPEG')
        self.itemRepository.create(item)
        try:
            self.itemRepository.create(item2)
        except Persistence.DuplicateEntryException, ex:
            assert 'MYID12435' == ex.duplicateId
        else:
            self.fail()
            
    def testSaveTwoDerivedItemsWithSameIDShouldThrowException(self):
        originalItem = Domain.OriginalItem('MYID12435', Domain.STATUS_OK, (800, 600), 'JPEG')
        item = Domain.DerivedItem(Domain.STATUS_OK, (100, 100), 'JPEG', originalItem)
        item2 = Domain.DerivedItem(Domain.STATUS_OK, (100, 100), 'JPEG', originalItem)
        
        self.itemRepository.create(originalItem)
        self.itemRepository.create(item)
            
        try:
            self.itemRepository.create(item2)
        except Persistence.DuplicateEntryException, ex:
            assert 'MYID12435-100x100' == ex.duplicateId
        else:
            self.fail()
        

def suite():
    return unittest.makeSuite(PersistenceTestCase, 'test')
