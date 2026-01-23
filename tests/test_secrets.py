import unittest
from unittest.mock import patch, MagicMock
from utils.secrets import get_secret

class TestSecrets(unittest.TestCase):
    @patch('utils.secrets.secretmanager.SecretManagerServiceClient')
    def test_get_secret(self, mock_client):
        mock_response = MagicMock()
        mock_response.payload.data = b'test-value'
        mock_client.return_value.access_secret_version.return_value = mock_response
        
        result = get_secret('test-secret')
        self.assertEqual(result, 'test-value')

if __name__ == '__main__':
    unittest.main()
