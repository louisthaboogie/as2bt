import unittest
import aerospike
import model_aerospike


class TestModelAerospike(unittest.TestCase):
    def setUp(self):
        self.aerospike_host = '35.237.70.157'
        self.aerospike_port = 3000

        self.namespace = 'test'
        self.set_name = 'books'

        self.key = 2

        self.config = {
            'hosts': [ (self.aerospike_host, self.aerospike_port) ]
        }

        self.client = aerospike.client(self.config).connect()

        self.test_data = {'id' : self.key, 'title' : 'test_title', 'author' : 'test_author', 
        'publishedDate' : 'test_published_date', 'imageUrl': 'test_image_url', 
        'description' : 'test_description', 'createdBy' : 'test_created_by', 
        'createdById' : 'test_created_by_id'}

        self.test_data_updated = {'id' : self.key, 'title' : 'updated_title', 'author' : 'test_author', 
        'publishedDate' : 'test_published_date', 'imageUrl': 'test_image_url', 
        'description' : 'test_description', 'createdBy' : 'test_created_by', 
        'createdById' : 'test_created_by_id'}


    def __testModelCreate__(self):
        model_aerospike.create(self.test_data, self.key)    
        self.assertNotEqual(dict(), model_aerospike.read(self.key))

    def __testModelRead__(self):
        data = model_aerospike.read(self.key)
        self.assertEqual(self.test_data, data)

    def __testModelList__(self):
        rows, next_key = model_aerospike.list()

        self.assertGreater(len(rows), 0)
        self.assertEqual(-1, next_key)

    def __testModelListByUser__(self):
        rows, next_key = model_aerospike.list_by_user(self.test_data['createdById'])
            
        self.assertGreater(len(rows), 0)
        self.assertEqual(-1, next_key)

    def __testModelUpdate__(self):
        model_aerospike.update(self.test_data_updated, self.key)
        updated = model_aerospike.read(self.key)

        self.assertEqual(self.test_data_updated, updated)

    def __testModelDelete__(self):
        model_aerospike.delete(self.key)
        self.assertEqual(dict(), model_aerospike.read(self.key))
    
    def testModel(self):
        self.__testModelCreate__()
        self.__testModelRead__()
        self.__testModelList__()
        self.__testModelListByUser__()
        self.__testModelUpdate__()
        self.__testModelDelete__()
        


if __name__ == '__main__':
    unittest.main()
