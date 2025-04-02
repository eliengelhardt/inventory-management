import unittest
from unittest.mock import patch, mock_open
import sys
import os
# Add the shipments directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shipments')))
import backup_inventory

class TestBackUpInventory(unittest.TestCase):

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=False)
    @patch('logging.info')
    @patch('logging.error')
    def test_create_directory(self, mock_error, mock_info, mock_exists, mock_makedirs):
        backup_inventory.create_directory('test_path')
        mock_makedirs.assert_called_once_with('test_path')
        mock_info.assert_any_call('Running method: create_directory for path test_path')
        mock_info.assert_any_call('Directory created: test_path')

    @patch('os.listdir', return_value=['file1.pkl', 'file2.pkl'])
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('logging.error')
    def test_load_pickle_files(self, mock_error, mock_pickle_load, mock_open, mock_listdir):
        mock_pickle_load.side_effect = [None, None]
        result = backup_inventory.load_pickle_files('test_path')
        self.assertTrue(result)

    @patch('os.listdir', return_value=['file1.pkl', 'file2.pkl'])
    @patch('os.path.isfile', return_value=True)
    @patch('shutil.copy2')
    @patch('os.path.exists', side_effect=lambda x: False)
    @patch('os.makedirs')
    @patch('logging.info')
    def test_copy_files(self, mock_info, mock_makedirs, mock_exists, mock_copy2, mock_isfile, mock_listdir):
        backup_inventory.copy_files('src_folder', 'dest_folder')
        mock_makedirs.assert_called_once_with('dest_folder')
        self.assertEqual(mock_copy2.call_count, 2)
        
        
    @patch('logging.info')
    @patch('logging.error')
    @patch('builtins.exit')
    @patch('backup_inventory.load_pickle_files', return_value=True)
    @patch('backup_inventory.copy_files')
    def test_before_run_success(self, mock_copy_files, mock_load_pickle_files, mock_exit, mock_error, mock_info):
        backup_inventory.before_run('test_path', 'test_path_copy')
        mock_info.assert_any_call('Running inventory backup...')
        mock_load_pickle_files.assert_any_call('test_path')
        mock_load_pickle_files.assert_any_call('test_path_copy')
        mock_copy_files.assert_called_once_with('test_path', 'test_path_copy')
        mock_exit.assert_not_called()


    @patch('logging.info')
    @patch('logging.error')
    @patch('builtins.exit')
    @patch('backup_inventory.load_pickle_files', side_effect=[True, False])
    @patch('backup_inventory.copy_files')
    def test_before_run_load_pickle_files_fail_copy(self, mock_copy_files, mock_load_pickle_files, mock_exit, mock_error, mock_info):
        backup_inventory.before_run('test_path', 'test_path_copy')
        mock_info.assert_any_call('Running inventory backup...')
        mock_load_pickle_files.assert_any_call('test_path')
        mock_load_pickle_files.assert_any_call('test_path_copy')
        mock_error.assert_called_once_with('Error: copied pickle files corrupted before run')
        mock_exit.assert_called_once()
        mock_copy_files.assert_called_once_with('test_path', 'test_path_copy')

    @patch('logging.info')
    @patch('logging.error')
    @patch('builtins.exit')
    @patch('backup_inventory.load_pickle_files', return_value=True)
    @patch('backup_inventory.copy_files', side_effect=Exception('Copy error'))
    def test_before_run_copy_files_exception(self, mock_copy_files, mock_load_pickle_files, mock_exit, mock_error, mock_info):
        backup_inventory.before_run('test_path', 'test_path_copy')
        mock_info.assert_any_call('Running inventory backup...')
        mock_load_pickle_files.assert_any_call('test_path')
        mock_error.assert_called_once_with('Error in deleting path test_path_copy')
        mock_exit.assert_not_called()
        mock_copy_files.assert_called_once_with('test_path', 'test_path_copy')

if __name__ == '__main__':
    unittest.main()