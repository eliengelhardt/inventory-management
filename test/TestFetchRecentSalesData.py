import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import os
import pickle
# Add the shipments directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shipments')))
import fetch_recent_sales_data
import json 

# Function to read JSON file and store its contents in a list
def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

class TestNewModule(unittest.TestCase):

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data=pickle.dumps({'key': 'value'}))
    @patch('pickle.load')
    def test_load_data(self, mock_pickle_load, mock_open, mock_exists):
        mock_pickle_load.return_value = {'key': 'value'}
        result = fetch_recent_sales_data.load_data('test_path')
        self.assertEqual(result, {'key': 'value'})
        mock_open.assert_called_once_with('test_path', 'rb')
        mock_pickle_load.assert_called_once()

    @patch('logging.debug')
    def test_identify_new_skus(self, mock_debug):
        existing_skus = ['sku1', 'sku2']
        all_skus = ['sku1', 'sku2', 'sku3', 'sku4']
        result = fetch_recent_sales_data.identify_new_skus(existing_skus, all_skus)
        self.assertEqual(result, ['sku3', 'sku4'])
        mock_debug.assert_called_once_with('New SKUs needing data: [\'sku3\', \'sku4\']')

    def test_get_sku_details(self):
        all_inventory = [
            {'sku': 'sku1', 'wpid': 'wpid1', 'productName': 'Product 1'},
            {'sku': 'sku2', 'wpid': 'wpid2', 'productName': 'Product 2'},
            {'sku': 'sku3', 'wpid': 'wpid3', 'productName': 'Product 3'}
        ]
        new_skus_need_data_for = ['sku2', 'sku3']
        result = fetch_recent_sales_data.get_sku_details(all_inventory, new_skus_need_data_for)
        expected_result = {
            'sku2': {
                'wpid': 'wpid2',
                'product_name': 'Product 2',
                'creation_timestamp': '',
                'if_mature': ''
            },
            'sku3': {
                'wpid': 'wpid3',
                'product_name': 'Product 3',
                'creation_timestamp': '',
                'if_mature': ''
            }
        }
        self.assertEqual(result, expected_result)



if __name__ == '__main__':
    unittest.main()