try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO  # noqa

from pystorages.exceptions import ImproperlyConfigured

from pystorages.backends.s3boto import S3BotoStorage, S3BotoStorageFile
from pystorages.conf import settings

try:
    from boto.gs.connection import GSConnection, SubdomainCallingFormat
    from boto.exception import GSResponseError
    from boto.gs.key import Key as GSKey
except ImportError:
    raise ImproperlyConfigured("Could not load Boto's Google Storage bindings.\n"
                               "See https://github.com/boto/boto")


class GSBotoStorageFile(S3BotoStorageFile):

    def write(self, content):
        if 'w' not in self._mode:
            raise AttributeError("File was not opened in write mode.")
        self.file = StringIO(content)
        self._is_dirty = True

    def close(self):
        if self._is_dirty:
            provider = self.key.bucket.connection.provider
            upload_headers = {provider.acl_header: self._storage.default_acl}
            upload_headers.update(self._storage.headers)
            self._storage._save_content(self.key, self.file, upload_headers)
        self.key.close()


class GSBotoStorage(S3BotoStorage):
    connection_class = GSConnection
    connection_response_error = GSResponseError
    file_class = GSBotoStorageFile
    key_class = GSKey

    access_key_names = ['GS_ACCESS_KEY_ID']
    secret_key_names = ['GS_SECRET_ACCESS_KEY']

    access_key = settings.get('GS_ACCESS_KEY_ID')
    secret_key = settings.get('GS_SECRET_ACCESS_KEY')
    file_overwrite = settings.get('GS_FILE_OVERWRITE', True)
    headers = settings.get('GS_HEADERS', {})
    bucket_name = settings.get('GS_BUCKET_NAME', None)
    auto_create_bucket = settings.get('GS_AUTO_CREATE_BUCKET', False)
    default_acl = settings.get('GS_DEFAULT_ACL', 'public-read')
    bucket_acl = settings.get('GS_BUCKET_ACL', default_acl)
    querystring_auth = settings.get('GS_QUERYSTRING_AUTH', True)
    querystring_expire = settings.get('GS_QUERYSTRING_EXPIRE', 3600)
    durable_reduced_availability = settings.get('GS_DURABLE_REDUCED_AVAILABILITY', False)
    location = settings.get('GS_LOCATION', '')
    custom_domain = settings.get('GS_CUSTOM_DOMAIN')
    calling_format = settings.get('GS_CALLING_FORMAT', SubdomainCallingFormat())
    secure_urls = settings.get('GS_SECURE_URLS', True)
    file_name_charset = settings.get('GS_FILE_NAME_CHARSET', 'utf-8')
    is_gzipped = settings.get('GS_IS_GZIPPED', False)
    preload_metadata = settings.get('GS_PRELOAD_METADATA', False)
    gzip_content_types = settings.get('GS_GZIP_CONTENT_TYPES', (
        'text/css',
        'application/javascript',
        'application/x-javascript',
    ))
    url_protocol = settings.get('GS_URL_PROTOCOL', 'http:')

    def _save_content(self, key, content, headers):
        # only pass backwards incompatible arguments if they vary from the default
        options = {}
        if self.encryption:
            options['encrypt_key'] = self.encryption
        key.set_contents_from_file(content, headers=headers,
                                   policy=self.default_acl,
                                   rewind=True, **options)

    def _get_or_create_bucket(self, name):
        """
        Retrieves a bucket if it exists, otherwise creates it.
        """
        if self.durable_reduced_availability:
            storage_class = 'DURABLE_REDUCED_AVAILABILITY'
        else:
            storage_class = 'STANDARD'
        try:
            return self.connection.get_bucket(name,
                validate=self.auto_create_bucket)
        except self.connection_response_error:
            if self.auto_create_bucket:
                bucket = self.connection.create_bucket(name, storage_class=storage_class)
                bucket.set_acl(self.bucket_acl)
                return bucket
            raise ImproperlyConfigured("Bucket %s does not exist. Buckets "
                                       "can be automatically created by "
                                       "setting GS_AUTO_CREATE_BUCKET to "
                                       "``True``." % name)
