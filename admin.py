from models import Burial, BurialImage
from flask_admin import Admin, form
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from wtforms import ValidationError, fields
from wtforms.validators import required
from wtforms.widgets import HTMLString, html_params, FileInput


# LargeBinary upload code lifted from
# http://stackoverflow.com/questions/33722132/storing-a-pdf-file-in-db-with-flask-admin
class BlobUploadField(fields.StringField):

    widget = FileInput()

    def __init__(self, label=None, allowed_extensions=None, size_field=None, filename_field=None, mimetype_field=None, **kwargs):

        self.allowed_extensions = allowed_extensions
        self.size_field = size_field
        self.filename_field = filename_field
        self.mimetype_field = mimetype_field
        #validators = [required()]
        validators=[]

        super(BlobUploadField, self).__init__(label, validators, **kwargs)

    def is_file_allowed(self, filename):
        """
            Check if file extension is allowed.

            :param filename:
                File name to check
        """
        if not self.allowed_extensions:
            return True

        return ('.' in filename and
                filename.rsplit('.', 1)[1].lower() in
                map(lambda x: x.lower(), self.allowed_extensions))

    def _is_uploaded_file(self, data):
        return data and data.filename

    def pre_validate(self, form):
        super(BlobUploadField, self).pre_validate(form)
        if self._is_uploaded_file(self.data) and not self.is_file_allowed(self.data.filename):
            raise ValidationError(gettext('Invalid file extension'))

    def process_formdata(self, valuelist):
        if valuelist:
            data = valuelist[0]
            self.data = data

    def populate_obj(self, obj, name):

        if self._is_uploaded_file(self.data):

            _blob = self.data.read()

            setattr(obj, name, _blob)

            if self.size_field:
                setattr(obj, self.size_field, len(_blob))

            '''
            if self.filename_field:
                setattr(obj, self.filename_field, self.data.filename)
                '''

            if self.mimetype_field:
                setattr(obj, self.mimetype_field, self.data.content_type)


class BurialModelView(ModelView):
    column_searchable_list = (Burial.last_name, Burial.first_name, \
        Burial.lot_owner, Burial.sd_type, Burial.sd, Burial.lot, Burial.space)


class BurialImageModelView(ModelView):
    form_extra_fields = {'data': BlobUploadField(
        label='File',
        allowed_extensions=['png', 'jpg', 'jpeg', 'gif'],
        size_field='size',
        filename_field='filename',
        mimetype_field='mimetype'
    )}

    def _download_formatter(self, context, model, name):
        return Markup("<a href='{url}' target='_blank'>Download</a>".format(url=self.get_url('download_image', id=model.id)))

    column_formatters = {
        'download': _download_formatter,
    }
