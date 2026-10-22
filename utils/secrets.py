"""
Google Secret Manager helper for secure credential storage.
"""

import os

from google.cloud import secretmanager

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')

def get_secret(secret_name, version='latest'):
    """
    Retrieve secret value from Secret Manager.

    Args:
        secret_name: Name of the secret
        version: Version number or 'latest'

    Returns:
        str: Secret value
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/{version}"

        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode('UTF-8')

    except Exception as e:
        raise Exception(f"Failed to retrieve secret '{secret_name}': {str(e)}") from e


def create_secret(secret_name, secret_value):
    """
    Create new secret in Secret Manager.

    Args:
        secret_name: Name for the secret
        secret_value: Value to store

    Returns:
        str: Secret resource name
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{PROJECT_ID}"

        # Create secret
        secret = client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_name,
                "secret": {"replication": {"automatic": {}}},
            }
        )

        # Add version
        client.add_secret_version(
            request={
                "parent": secret.name,
                "payload": {"data": secret_value.encode('UTF-8')},
            }
        )

        return secret.name

    except Exception as e:
        raise Exception(f"Failed to create secret: {str(e)}") from e
