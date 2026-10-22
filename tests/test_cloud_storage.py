"""
Tests for Cloud Storage integration
"""

import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image

from main import app


class TestCloudStorage(unittest.TestCase):
    """Test Cloud Storage image upload functionality"""

    def setUp(self):
        """Set up test client with admin session"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Admin'
            sess['is_admin'] = True

    def create_test_image(self):
        """Create a valid test image in memory"""
        img = Image.new('RGB', (100, 100), color='red')
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        return img_byte_arr

    @patch('utils.cloud_storage.storage.Client')
    def test_upload_image_success(self, mock_storage_client):
        """Test successful image upload to Cloud Storage"""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.public_url = 'https://storage.googleapis.com/buffetier-menu-images/menu-items/test.jpg'

        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        test_image = self.create_test_image()

        response = self.client.post(
            '/admin/api/upload-image',
            data={'image': (test_image, 'test.jpg')},
            content_type='multipart/form-data'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json.get('success'))
        self.assertIn('url', response.json)
        self.assertIn('storage.googleapis.com', response.json['url'])

    def test_upload_no_file(self):
        """Test upload endpoint returns error when no file provided"""
        response = self.client.post('/admin/api/upload-image')

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertIn('No image file', data['error'])

    def test_upload_empty_filename(self):
        """Test upload endpoint returns error for empty filename"""
        response = self.client.post(
            '/admin/api/upload-image',
            data={'image': (BytesIO(b''), '')},
            content_type='multipart/form-data'
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    @patch('utils.cloud_storage.storage.Client')
    def test_upload_invalid_file_type(self, mock_storage_client):
        """Test upload rejects invalid file types"""
        test_file = BytesIO(b'not an image')

        response = self.client.post(
            '/admin/api/upload-image',
            data={'image': (test_file, 'test.txt')},
            content_type='multipart/form-data'
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    @patch('utils.cloud_storage.storage.Client')
    def test_delete_image_success(self, mock_storage_client):
        """Test successful image deletion"""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.exists.return_value = True

        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        response = self.client.post(
            '/admin/api/delete-image',
            json={'image_url': 'https://storage.googleapis.com/buffetier-menu-images/menu-items/test.jpg'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json.get('success'))

    def test_delete_no_url(self):
        """Test delete endpoint returns error when no URL provided"""
        response = self.client.post('/admin/api/delete-image', json={})

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    def test_unauthorized_access(self):
        """Test non-admin users cannot access upload endpoint"""
        with self.client.session_transaction() as sess:
            sess.clear()

        test_image = self.create_test_image()

        response = self.client.post(
            '/admin/api/upload-image',
            data={'image': (test_image, 'test.jpg')},
            content_type='multipart/form-data'
        )

        self.assertIn(response.status_code, [302, 308, 403])


if __name__ == '__main__':
    unittest.main()
