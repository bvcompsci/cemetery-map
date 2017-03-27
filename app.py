from flask import abort, Flask, json, redirect, \
                    render_template, request, Response, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from errors import *
import os
import random
import string


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


UPLOAD_FOLDER = 'static/images/headstone'
ALLOWED_IMAGE_EXTENSIONS = set(['jpg','gif','png'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_DATA_EXTENSIONS = set(['csv','zip'])

DOWNLOAD_FOLDER = 'static/download'
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER


from models import Burial, BurialImage, BurialJSONEncoder, get_burials, get_burial, \
    add_burial, remove_all_burials, get_burial_images, get_burial_image, \
    add_burial_image, set_latlng


from admin import Admin, BurialModelView, BurialImageModelView

admin = Admin(app, name='cemetery-map', template_mode='bootstrap3')
admin.add_view(BurialModelView(Burial, db.session))
admin.add_view(BurialImageModelView(BurialImage, db.session))


def randstr():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) \
                for _ in range(30))


def allowed_image_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_IMAGE_EXTENSIONS


def allowed_data_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_DATA_EXTENSIONS


def split_csv_line(line):
    buf = ''
    cols = []
    in_quotes = False
    for i in range(0, len(line)):
        if line[i] == ',' and not in_quotes:
            cols.append(buf)
            buf = ''
        elif line[i] == '"':
            in_quotes = not in_quotes
        else:
            buf = buf + str(line[i])

    if buf == '\r':
        cols.append('')
    elif buf != '':
        cols.append(buf)

    # The CSV file may not have lat/lng values.
    # If not, give it defaults of 0,0.

    while len(cols) < 22:
        cols.append(0)

    return cols


@app.route('/')
def index():
    '''Downloads the initial map page.
    '''
    return render_template('index.html')


@app.route('/headstones/<int:burial_id>', methods=['GET'])
def images_iframe_content(burial_id):
    '''Returns an HTML snippet containing all headstone images for the given
       burial_id, or a single 'no image' image if the burial_id has no
       associated headstone images.  This URL is referenced in static/js/map.js.
    '''
    html = ''
    burial_images = get_burial_images(burial_id)
    if len(burial_images) == 0:
        return '<img style="width: 200px;" src="' \
              + url_for('no_image') \
              + '"><br>'
    for bi in burial_images:
        html += '<img style="width: 200px;" src="' \
              + url_for('download_image', burial_id=burial_id, image_id=bi.id) \
              + '"><br>'
    return html


@app.route('/api/search', methods=['GET', 'POST'])
def search():
    '''Returns a JSON list of matching burials or an error string on failure.
    If no form key/value pairs are specified, *ALL* burials are returned.
    This includes purchased plots that do not yet have a burial.
    '''
    try:
        js = json.dumps(get_burials(request.form), cls=BurialJSONEncoder)
        resp = Response(js, status=200, mimetype='application/json')
        return resp
    except Exception as e:
        return ERR_GENERAL


@app.route('/api/headstone/<int:burial_id>/<int:image_id>', methods=['GET'])
def download_image(burial_id, image_id):
    '''Retrieves image corresponding to the burial ID provided in the URL.
    This URL will most likely be specified in HTML as the 'src' attribute
    of an 'img' tag.
    '''
    target = app.config['HS_IMAGE_TARGET']
    bi = get_burial_image(image_id)
    if bi == None:
        abort(404)
    elif target == 'file':
        return redirect( \
            os.path.join(app.config['UPLOAD_FOLDER'], bi.filename), code=302)
    elif target == 'db':
        return app.response_class(bi.data, mimetype='application/octet-stream')


@app.route('/api/headstone/none', methods=['GET'])
def no_image():
    '''URL referenced by images_iframe_content() if a burial has no
       headstone images associated with it.
    '''
    return redirect( \
            os.path.join(app.config['UPLOAD_FOLDER'], 'no-image.png'), \
            code=302)


@app.route('/api/headstone/<int:burial_id>', methods=['POST'])
def upload_image(burial_id):
    '''Given an HTML form with enctype=multipart/form-data and an input
    type=file, this REST endpoint places a headstone image file into
    the upload folder UPLOAD_FOLDER and then updates the database
    with the new filename.

    This function is typically called directly by another route, such as
    POST /api/update-burial.
    '''

    if not get_burial(burial_id):
        return ERR_NO_SUCH_BURIAL

    try:
        if 'file' not in request.files:
            return ERR_NO_FILE_SPECIFIED
        infile = request.files['file']
        if infile.filename == '':
            return ERR_NO_FILE_SPECIFIED

        target = app.config['HS_IMAGE_TARGET']
        if infile and allowed_image_file(infile.filename):
            filename = secure_filename(infile.filename)
            suffix = filename[filename.rindex('.'):]
            filename = 'hs-' + randstr() + '-' + str(burial_id) + suffix
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            add_burial_image( \
                burial_id, \
                filename if target == 'file' else None, \
                infile.read() if target == 'db' else None)

            if target == 'file':
                infile.save(filepath)
        else:
            return ERR_NOT_IMAGE
    except Exception as e:
        print('Error: {}'.format(str(e)))
        return ERR_GENERAL

    return 'ok'


@app.route('/api/data', methods=['GET'])
def database_download():
    '''Retrieves a CSV file containing all database data.  The filename
    will contain the date on which the request was completed.

    In a future version, this REST endpoint will retrieves a
    ZIP file containing a CSV of all database data
    and all headstone image files.
    '''

    if not os.path.isdir(app.config['DOWNLOAD_FOLDER']):
        os.mkdir(app.config['DOWNLOAD_FOLDER'])

    from time import gmtime, strftime
    filename = 'cemdb-'+strftime('%Y%m%d-%H%M%S', gmtime())+'.csv'
    pathname = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)

    with open(pathname, 'w') as csv_file:
        csv_file.write( \
            'id,sd_type,sd,lot,space,lot_owner,year_purch,first_name,' +
            'last_name,sex,birth_date,birth_place,death_date,age,' +
            'death_place,death_cause,burial_date,notes,more_notes,' +
            'hidden_notes,lat,lng\n' )

        burials = get_burials()

        for burial in burials:
            csv_file.write(str(burial.id)+',')
            csv_file.write('"'+burial.sd_type+'",')
            csv_file.write('"'+burial.sd+'",')
            csv_file.write('"'+burial.lot+'",')
            csv_file.write('"'+burial.space+'",')
            csv_file.write('"'+burial.lot_owner+'",')
            csv_file.write('"'+burial.year_purch+'",')
            csv_file.write('"'+burial.first_name+'",')
            csv_file.write('"'+burial.last_name+'",')
            csv_file.write('"'+burial.sex+'",')
            csv_file.write('"'+burial.birth_date+'",')
            csv_file.write('"'+burial.birth_place+'",')
            csv_file.write('"'+burial.death_date+'",')
            csv_file.write('"'+burial.age+'",')
            csv_file.write('"'+burial.death_place+'",')
            csv_file.write('"'+burial.death_cause+'",')
            csv_file.write('"'+burial.burial_date+'",')
            csv_file.write('"'+burial.notes+'",')
            csv_file.write('"'+burial.more_notes+'",')
            csv_file.write('"'+burial.hidden_notes+'",')
            csv_file.write(str(burial.lat)+',')
            csv_file.write(str(burial.lng)+'\n')

    return redirect(pathname, code=302)


@app.route('/api/data', methods=['DELETE'])
def database_nuke():
    '''Nukes all data in the DB.  This route is only available in
    Development, not in Test or Production.
    '''
    if 'DEVELOPMENT' in app.config:
        remove_all_burials()
        return 'ok'
    else:
        abort(404)


@app.route('/api/data', methods=['POST'])
def database_upload():
    '''Reloads all application data from a CSV file.  CSV file should be
    sent as form-data using the key 'file'.

    In a future version, this REST endpoint will reload all
    application data from a ZIP file containing
    a CSV of all database data and all headstone images.
    '''

    if 'file' not in request.files:
        return ERR_NO_FILE_SPECIFIED

    file = request.files['file']
    if file.filename == '':
        return ERR_NO_FILE_SPECIFIED

    if file and allowed_data_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(filename)

        remove_all_burials()

        import codecs
        with codecs.open(filename, 'r', encoding='utf-8', \
            errors='ignore') as csv_file:

            # Assume there's a header line and ignore it.
            lines = csv_file.readlines()[1:]

            # Add a burial DB row for each line in the CSV file.
            # ID columns in the CSV file are ignored.
            for line in lines:
                col_values = split_csv_line(line)
                add_burial({
                    'sd_type' : col_values[1],
                    'sd' : col_values[2],
                    'lot' : col_values[3],
                    'space' : col_values[4],
                    'lot_owner' : col_values[5],
                    'year_purch' : col_values[6],
                    'first_name' : col_values[7],
                    'last_name' : col_values[8],
                    'sex' : col_values[9],
                    'birth_date' : col_values[10],
                    'birth_place' : col_values[11],
                    'death_date' : col_values[12],
                    'age' : col_values[13],
                    'death_place' : col_values[14],
                    'death_cause' : col_values[15],
                    'burial_date' : col_values[16],
                    'notes' : col_values[17],
                    'more_notes' : col_values[18],
                    'hidden_notes' : col_values[19],
                    'lat' : col_values[20],
                    'lng' : col_values[21],
                })

    return 'ok - %d burials loaded' % len(lines)


@app.route('/api/burial-summary', methods=['GET'])
def burial_summary():
    '''This REST endpoint is used by the Android camera app 'cemetery-cam'
    to retrieve a subset of burial information for all burials
    in the cemetery.  This subset is represented by a JSON array objects

        {
            id: ID,
            first_name: FNAME,
            last_name: LNAME,
            birth_date: BDATE,
            death_date : DDATE
        }

    where the CAPS strings represent the actual values returned.  Only actual
    burials are returned.  Plots without an actual burial are excluded from
    the returned list.  Callers can expect the burials to be alphabetized by
    last_name.

    This information is used by the camera app to select a burial prior to
    filling in its headstone photo and latitude/longitude.  The headstone photo
    and latitude/longitude get uploaded using the POST /api/update-burial REST
    endpoint.
    '''
    try:
        burials = get_burials()
        burials_less = []
        for burial in burials:
            burials_less.append({
                'id': burial.id,
                'first_name': burial.first_name,
                'last_name': burial.last_name,
                'birth_date': burial.birth_date,
                'death_date': burial.death_date,
            })

        burials_less = sorted( \
            list(filter(lambda b: b['last_name'] != "", burials_less)), \
            key=lambda b: b['last_name'])

        js = json.dumps(burials_less, cls=BurialJSONEncoder)
        resp = Response(js, status=200, mimetype='application/json')
        return resp
    except Exception as e:
        return ERR_GENERAL


@app.route('/api/update-burial', methods=['POST'])
def update_burial():
    '''This REST endpoint is used by the Android camera app 'cemetery-cam'
    to update the latitude, longitude, and headstone image given a certain
    burial ID.
    '''
    set_latlng(request.form['id'], request.form['lat'], request.form['lng'])
    upload_image(request.form['id'])
    return 'ok'


from models import make_dummy_data

@app.route('/api/add-test-latlng', methods=['GET', 'POST'])
def add_test_data():
    make_dummy_data()
    return 'ok'


if __name__ == '__main__':
    print('Using environment', os.environ['APP_SETTINGS'])
    app.run()
