import os
import unittest
import json

from app import app, db
from models import Burial, BurialImage, add_burial

SQLITE_DB_PATH = 'data/cemdb-test.db'
TEST_BURIAL_ID = 1
TEST_LAT = 42.641333
TEST_LNG = -95.211234
TEST_IMAGE_PATHNAME = 'static/images/samples/hs-anderson.jpg'
TEST_IMAGE_FILENAME = 'hs-anderson.jpg'


class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + SQLITE_DB_PATH
        self.client = app.test_client()
        db.create_all()
        self.create_test_data()


    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.remove(SQLITE_DB_PATH)


    def create_test_data(self):
        '''Creates test burial objects, keeps them resident in
           self.test_burials, and adds them to the temporary test DB.
        '''
        self.test_burials = [
            dict(first_name='Stewey', last_name='Anderson'),
            dict(first_name='Linus', last_name='Anderson'),
            dict(first_name='Linus', last_name='Smith'),
        ]

        for b in self.test_burials:
            add_burial(b)


    def test_api_search(self):
        '''Tests the Search API both with and without parameters.
           Searching without parameters should return all burial records.
        '''
        res = self.client.post('/api/search', data=dict(last_name='Anderson'))
        list_from_api = json.loads(str(res.get_data(), encoding='utf-8'))
        list_from_test_burials = [b for b in self.test_burials
                                    if b['last_name'] == 'Anderson']
        assert len(list_from_api) == len(list_from_test_burials)

        res = self.client.post('/api/search', data={})
        list_all_from_api = json.loads(str(res.get_data(), encoding='utf-8'))
        assert len(list_all_from_api) == len(self.test_burials)


    def test_integ_camera_get(self):
        '''Ensures camera integration REST endpoint burial-summary
           returns all burials with the prescribed reduced subset
           of attributes.
        '''
        res = self.client.get('/api/burial-summary')
        list_from_api = json.loads(str(res.get_data(), encoding='utf-8'))
        assert len(list_from_api) == len(self.test_burials)
        assert len(list_from_api) > 0
        first_burial = list_from_api[0]
        assert 'id' in first_burial
        assert 'first_name' in first_burial
        assert 'last_name' in first_burial
        assert 'birth_date' in first_burial
        assert 'death_date' in first_burial


    def test_integ_camera_post(self):
        # Do a POST to /api/update-burial.
        with open(TEST_IMAGE_PATHNAME, 'rb') as test_image_file:
            res_update = self.client.post('/api/update-burial',
                data=dict(
                    id=str(TEST_BURIAL_ID),
                    lat=str(TEST_LAT),
                    lng=str(TEST_LNG),
                    file=(test_image_file, TEST_IMAGE_FILENAME),
                ))

        # Check the integrity of the POST.  Determine whether it was
        # successful using other API calls.

        # First, check the lat/lng.
        res_search = self.client.get('/api/search',
                                     data=dict(id=TEST_BURIAL_ID))
        burial_list = json.loads(str(res_search.get_data(), encoding='utf-8'))
        assert len(burial_list) == 1
        single_burial = burial_list[0]
        assert single_burial['lat'] == TEST_LAT
        assert single_burial['lng'] == TEST_LNG

        # Then, check the headstone image to see if the image retrieved from
        # the API matches the image from the filesystem.
        res_image_ids = self.client.get('/api/headstones/{}'
                                        .format(TEST_BURIAL_ID))
        image_ids = json.loads(str(res_image_ids.get_data(), encoding='utf-8'))
        image_id = image_ids[0]
        res_image = self.client.get('/api/headstone/{}/{}'
                                    .format(TEST_BURIAL_ID, image_id))
        image_data_from_api = res_image.get_data()
        with open(TEST_IMAGE_PATHNAME, 'rb') as test_image_file:
            image_data_from_disk = test_image_file.read()
            assert image_data_from_api == image_data_from_disk


if __name__ == '__main__':
    unittest.main()
