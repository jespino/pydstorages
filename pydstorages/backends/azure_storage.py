import os.path

from pydstorages.base import ContentFile
from pydstorages.storage import Storage
from pydstorages.exceptions import ImproperlyConfigured

try:
    import azure
    import azure.storage
except ImportError:
    raise ImproperlyConfigured(
        "Could not load Azure bindings. "
        "See https://github.com/WindowsAzure/azure-sdk-for-python")

from pydstorages.conf import settings


def clean_name(name):
    return os.path.normpath(name).replace("\\", "/")


class AzureStorage(Storage):
    account_name = settings.get("AZURE_ACCOUNT_NAME")
    account_key = settings.get("AZURE_ACCOUNT_KEY")
    azure_container = settings.get("AZURE_CONTAINER")

    def __init__(self, *args, **kwargs):
        super(AzureStorage, self).__init__(*args, **kwargs)
        self._connection = None

    @property
    def connection(self):
        if self._connection is None:
            self._connection = azure.storage.BlobService(
                self.account_name, self.account_key)
        return self._connection

    def _open(self, name, mode="rb"):
        contents = self.connection.get_blob(self.azure_container, name)
        return ContentFile(contents)

    def exists(self, name):
        try:
            self.connection.get_blob_properties(
                self.azure_container, name)
        except azure.WindowsAzureMissingResourceError:
            return False
        else:
            return True

    def delete(self, name):
        self.connection.delete_blob(self.azure_container, name)

    def size(self, name):
        properties = self.connection.get_blob_properties(
            self.azure_container, name)
        return properties["content-length"]

    def _save(self, name, content):
        self.connection.put_blob(self.azure_container, name,
                                 content, "BlockBlob")
        return name

    def url(self, name):
        return "%s/%s" % (self.azure_bucket, name)
