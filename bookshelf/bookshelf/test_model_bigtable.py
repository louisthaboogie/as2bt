from google.cloud import bigtable
from google.cloud.bigtable import row_filters

import unittest
import model_bigtable


class TestModelBigtable(unittest.TestCase):
    def setUp(self):
        self.project_id = 'aerospike2bt'
        self.instance_id = 'bookshelf'
        self.table_id = 'books'

        self.client = bigtable.Client(project=self.project_id, admin=True)
        self.instance = self.client.instance(self.instance_id)
        self.table = self.instance.table(self.table_id)

        self.cf = 'info'
        self.title = 'title'.encode()
        self.author = 'author'.encode() 
        self.published_date = 'published_date'.encode() 
        self.image_url = 'image_url'.encode()
        self.description = 'description'.encode()
        self.created_by = 'created_by'.encode()  
        self.created_by_id = 'created_by_id'.encode()

        self.row_filter = row_filters.CellsColumnLimitFilter(1)

        self.test_data = {'id': '123456789', 'title': 'test_title', 'author': 'test_author', 
        'publishedDate': 'test_published_date', 'imageUrl': 'test_image_url', 
        'description': 'test_description', 'createdBy': 'test_created_by', 
        'createdById': 'test_created_by_id'}

        self.test_data_updated = {'id': '123456789', 'title': 'updated_title', 'author': 'test_author', 
        'publishedDate': 'test_published_date', 'imageUrl': 'test_image_url', 
        'description': 'test_description', 'createdBy': 'test_created_by', 
        'createdById': 'test_created_by_id'}

        self.row_key = (self.test_data['createdById'] + '_' + self.test_data['id']).encode()

    def __testCreateAPI__(self):
        row = self.table.row(self.row_key)

        rows = []

        row.set_cell(self.cf, self.title, 'test_title')
        row.set_cell(self.cf, self.author, 'test_author')
        row.set_cell(self.cf, self.published_date, 'test_published_date')
        row.set_cell(self.cf, self.image_url, 'test_image_url')
        row.set_cell(self.cf, self.description, 'test_description')
        row.set_cell(self.cf, self.created_by, 'test_created_by')
        row.set_cell(self.cf, self.created_by_id, 'test_created_by_id')

        rows.append(row)

        self.table.mutate_rows(rows)
        self.assertIsNotNone(self.table.read_row(self.row_key))

    def __testReadAPI__(self):
        row = self.table.read_row(self.row_key, self.row_filter)
        row_key = row.row_key.decode('utf-8')
        info_cells = row.cells[self.cf]

        title_val = info_cells[self.title][0].value.decode('utf-8')
        author_val = info_cells[self.author][0].value.decode('utf-8')
        published_date_val = info_cells[self.published_date][0].value.decode('utf-8')
        image_url_val = info_cells[self.image_url][0].value.decode('utf-8')
        description_val = info_cells[self.description][0].value.decode('utf-8')
        created_by_val = info_cells[self.created_by][0].value.decode('utf-8')
        created_by_id_val = info_cells[self.created_by_id][0].value.decode('utf-8')

        self.assertEqual(self.row_key.decode('utf-8'), row_key)
        self.assertEqual('test_title', title_val)
        self.assertEqual('test_author', author_val)
        self.assertEqual('test_published_date', published_date_val)
        self.assertEqual('test_image_url', image_url_val)
        self.assertEqual('test_description', description_val)
        self.assertEqual('test_created_by', created_by_val)
        self.assertEqual('test_created_by_id', created_by_id_val)

    def __testUpdateAPI__(self):
        row = self.table.row(self.row_key)
        row.set_cell(self.cf, self.title, 'updated_title') 
        row.commit()

        updated_row = self.table.read_row(self.row_key, self.row_filter)
        self.assertEqual('updated_title', updated_row.cells[self.cf][self.title][0].value.decode('utf-8'))

    def __testDeleteAPI__(self):
        row = self.table.row(self.row_key)

        self.assertIsNotNone(self.table.read_row(self.row_key, self.row_filter))
        row.delete()
        row.commit()

        self.assertIsNone(self.table.read_row(self.row_key, self.row_filter))        

    def testAPI(self):
        self.__testCreateAPI__()
        self.__testReadAPI__()
        self.__testUpdateAPI__()
        self.__testDeleteAPI__() 

    def __testModelCreate__(self):
        model_bigtable.create(self.test_data)
        self.assertNotEqual(dict(), model_bigtable.read(self.row_key))

    def __testModelRead__(self):
        data = model_bigtable.read(self.row_key)
        self.assertEqual(self.test_data, data)
    
    def __testModelUpdate__(self):
        model_bigtable.update(self.test_data_updated, self.row_key)
        updated = model_bigtable.read(self.row_key)

        self.assertEqual(self.test_data_updated, updated)

    def __testModelDelete__(self):
        model_bigtable.delete(self.row_key)
        self.assertEqual(dict(), model_bigtable.read(self.row_key))

    def __testModelList__(self):
        rows, last_key = model_bigtable.list(limit=1)
        self.assertEqual(1, len(rows))
       
    def __testModelListByUser__(self):
        rows, last_key = model_bigtable.list_by_user(self.test_data['createdById'])
        
        self.assertEqual(1, len(rows))
        self.assertEqual(self.test_data, rows[0])
        
    def testModel(self):
        self.__testModelCreate__()
        self.__testModelRead__()
        self.__testModelList__()
        self.__testModelListByUser__()
        self.__testModelUpdate__()
        self.__testModelDelete__()


if __name__ == '__main__':
    unittest.main()
