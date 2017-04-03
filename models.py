from app import db
from json import JSONEncoder


class Burial(db.Model):
    __tablename__ = 'burials'

    # Most columns are strings--even dates--because a city's data
    # is often free-form in cases where dates are fuzzy,
    # e.g., '1960?' (note the question mark).
    id = db.Column(db.Integer, primary_key=True)
    sd_type = db.Column(db.String())
    sd = db.Column(db.String())
    lot = db.Column(db.String())
    space = db.Column(db.String())
    lot_owner = db.Column(db.String())
    year_purch = db.Column(db.String())
    last_name = db.Column(db.String())
    first_name = db.Column(db.String())
    sex = db.Column(db.String())
    birth_date = db.Column(db.String())
    birth_place = db.Column(db.String())
    death_date = db.Column(db.String())
    age = db.Column(db.String())
    death_place = db.Column(db.String())
    death_cause = db.Column(db.String())
    burial_date = db.Column(db.String())
    notes = db.Column(db.String())
    more_notes = db.Column(db.String())
    hidden_notes = db.Column(db.String())
    lat = db.Column(db.Float())
    lng = db.Column(db.Float())

    def __repr__(self):
        return '<burial id=%d, last_name=%s, first_name=%s ...>' % \
            (self.id, self.last_name, self.first_name)


class BurialImage(db.Model):
    __tablename__ = 'burial_images'

    id = db.Column(db.Integer, primary_key=True)
    burial_id = db.Column(db.Integer, db.ForeignKey('burials.id'))
    burial = db.relationship('Burial',
                             backref=db.backref('burial_images',
                                                lazy='dynamic'))

    # Depending on deployment environment, we may choose to store images in the
    # filesystem or in the DB.  We will maintain columns for both and then rely
    # on the Flask app config object to tell us which we should use.
    filename = db.Column(db.String())
    data = db.Column(db.LargeBinary)


class BurialJSONEncoder(JSONEncoder):
    def default(self, o):
        d = o.__dict__

        # Remove values that are not JSON serializable.
        if '_sa_instance_state' in d:
            del d['_sa_instance_state']

        return d


def get_burials(columns_dict={}):
    """Retrieves burials matching the given dictionary criteria.
    If no arguments or an empty dictionary is given, all burials will
    be returned.
    """
    q = Burial.query
    for attr, value, in columns_dict.items():
        if value != "":
            q = q.filter(getattr(Burial, attr).like("%%%s%%" % value))
    return q.all()


def get_burial(id):
    return Burial.query.filter(Burial.id == id).first()


def add_burial(columns_dict):
    b = Burial(**columns_dict)
    db.session.add(b)
    db.session.commit()


def remove_all_burials():
    Burial.query.delete()
    BurialImage.query.delete()
    db.session.commit()
    db.engine.execute('alter sequence burials_id_seq RESTART with 1')
    db.engine.execute('alter sequence burial_images_id_seq RESTART with 1')


def get_burial_images(burial_id=None):
    if burial_id is None:
        return BurialImage.query.all()

    return BurialImage.query.filter(BurialImage.burial_id == burial_id).all()


def get_burial_image(image_id):
    return BurialImage.query.filter(BurialImage.id == image_id).first()


def add_burial_image(burial_id, filename, data):
    bi = BurialImage()
    bi.burial_id = burial_id
    bi.filename = filename
    bi.data = data
    db.session.add(bi)
    db.session.commit()


def set_latlng(the_id, lat, lng):
    burial = get_burial(the_id)
    burial.lat = lat
    burial.lng = lng
    db.session.commit()


def make_dummy_data():
    b = get_burial(1)
    b.lat = 42.634739
    b.lng = -95.173137
    db.session.commit()

    b = get_burial(2)
    b.lat = 42.634639
    b.lng = -95.173237
    db.session.commit()

    b = get_burial(3)
    b.lat = 42.633739
    b.lng = -95.175087
    db.session.commit()

    b = get_burial(1878)
    b.lat = 42.633839
    b.lng = -95.175187
    db.session.commit()

    b = get_burial(1879)
    b.lat = 42.633939
    b.lng = -95.175287
    db.session.commit()
