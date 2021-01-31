"""
Storage system to store media files in Wasabi
"""


from .s3 import S3StorageSystem


class WasabiStorageSystem(S3StorageSystem):
    # Disable abstract class warning
    # pylint: disable=W0223

    def __init__(self, base=None, storage=None):
        super(WasabiStorageSystem, self).__init__(
            base,
            storage,
            s3args=dict(
                access_key=storage.credential_id,
                secret_key=storage.credential_key,
                host='s3.wasabisys.com',
            )
        )
