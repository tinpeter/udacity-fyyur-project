#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

# import datetime
from datetime import datetime
import json
import dateutil.parser
import babel
import sys
import re
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from sqlalchemy import Identity
from flask_wtf import Form
from forms import *
# from datetime import timedelta
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Common data.
current_date = babel.dates.format_datetime(datetime.now(), "medium", locale='en')

#----------------------------------------------------------------------------#
# Models.
Show = db.Table('show', 
  db.Column('artist_id',db.Integer, db.ForeignKey('Artist.id'), primary_key = True),
  db.Column('venue_id',db.Integer, db.ForeignKey('Venue.id'), primary_key = True),
  db.Column('start_time', db.String(120))
)

#----------------------------------------------------------------------------#
class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(
      db.Integer,Identity(start=1, increment=1,minvalue=1,nomaxvalue=True ,cycle=True) ,primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(300))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(
      db.Integer, Identity(start=1, increment=1,minvalue=1,nomaxvalue=True ,cycle=True) ,primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_description = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean(), default = True)
    venue_id = db.relationship('Venue',secondary = Show, backref=db.backref('Artist', lazy=True))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
# app.app_context().push()
# db.create_all()

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data_list = Venue.query.all()
  categories = []
  for item in data_list:
    venue = {
      'id': item.id,
      'name': item.name,
    }
    findCurrent = next((c for c in categories if c['city'] == item.city and c['state'] == item.state), None)
    if findCurrent:
      findCurrent['venues'].append(venue)
    else:
      city = {
        'city': item.city,
        'state': item.state,
        'venues': [venue]
      }
      categories.append(city)

  return render_template('pages/venues.html', areas=categories)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  venue_list = Venue.query.all()
  search_term = request.form.get('search_term').lower()
  data_list = []
  for venue in venue_list:
    if search_term in venue.name.lower():
      data_list.append(venue)

  response={
    "count": len(data_list),
    "data": data_list,
    "num_upcoming_shows": 0
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.filter_by(id = venue_id).all()[0]
  data_list = db.session.query(Show).filter_by(venue_id = venue.id).all()
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(","),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": commonDef(current_date, data_list, 'venue')["past_shows_list"],
    "upcoming_shows": commonDef(current_date, data_list, 'venue')["upcoming_shows_list"],
    "past_shows_count": commonDef(current_date, data_list, 'venue')["past_shows"],
    "upcoming_shows_count": commonDef(current_date, data_list, 'venue')["upcoming_shows"],
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  try:
    form = VenueForm(request.form)
    data = Venue(
      name = form.name.data, city = form.city.data,
      state = form.state.data, address = form.address.data, phone = form.phone.data,
      genres = '', image_link = form.image_link.data, facebook_link = form.facebook_link.data,
      website = form.website_link.data, seeking_description = form.seeking_description.data, seeking_talent = form.seeking_talent.data
    )
    for item in enumerate(form.genres.data):
      if item[0] != (len(form.genres.data) - 1):
        data.genres += item[1] + ', '
      else:
        data.genres += item[1]
  except:
    # on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    print(sys.exc_info())
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    db.session.add(data)
    db.session.commit()
    db.session.close()
  # TODO: modify data to be the data object returned from db insertion
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/delete', methods=['DELETE','POST','GET'])
# @app.route('/artists/<int:artist_id>')
def delete_venue(venue_id):
  print("venue_id", venue_id)
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
      data_delete_id = venue_id
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.query(Show).filter_by(venue_id = data_delete_id).delete()
      db.session.commit()
      flash('Venue ' + str(venue_id) + ' was successfully removed!')
  except():
    print(sys.exc_info())
    db.session.rollback()
  finally:
      db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect('/')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  try:
    data = []
    for item in Artist.query.order_by(db.asc(Artist.id)).all():
      data.append({
        'id': item.id,
        'name': item.name
      })
  except:
    print(sys.exc_info())
  finally:
    db.session.close()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  artists = Artist.query.all()
  search_term = request.form.get('search_term').lower()
  list_data = []
  for artist in artists:
    if search_term in artist.name.lower():
      list_data.append(artist)

  response={
    "count": len(list_data),
    "data": list_data,
    "num_upcoming_shows": 0
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.filter_by(id = artist_id).all()[0]
  data_list = db.session.query(Show).filter_by(artist_id = artist.id).all()
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(","),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": commonDef(current_date, data_list, 'artist')["past_shows_list"],
    "upcoming_shows": commonDef(current_date, data_list, 'artist')["upcoming_shows_list"],
    "past_shows_count": commonDef(current_date, data_list, 'artist')["past_shows"],
    "upcoming_shows_count": commonDef(current_date, data_list, 'artist')["upcoming_shows"],
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  edit_artist = Artist.query.filter_by(id = artist_id).all()[0]
  artist={
    "id": edit_artist.id,
    "name": edit_artist.name,
    "genres": edit_artist.genres.split(","),
    "city": edit_artist.city,
    "state": edit_artist.state,
    "phone": edit_artist.phone,
    "website": edit_artist.website,
    "facebook_link": edit_artist.facebook_link,
    "seeking_venue": edit_artist.seeking_venue,
    "seeking_description":  edit_artist.seeking_description,
    "image_link": edit_artist.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  form = ArtistForm(
    name = artist["name"], genres = artist["genres"], city = artist["city"],
    state = artist["state"], phone = artist["phone"], website_link = artist["website"],
    facebook_link = artist["facebook_link"], seeking_venue = artist["seeking_venue"],
    seeking_description = artist["seeking_description"], image_link = artist["image_link"]
  )
  return render_template('forms/edit_artist.html', form=form, artist=artist)

#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    submit_form = ArtistForm(request.form)
    edit_data = Artist.query.get(artist_id)
    edit_data.name = submit_form.name.data
    edit_data.genres = str(",").join(submit_form.genres.data)
    edit_data.city = submit_form.city.data
    edit_data.state = submit_form.state.data
    edit_data.phone = submit_form.phone.data
    edit_data.website = submit_form.website_link.data
    edit_data.facebook_link = submit_form.facebook_link.data
    edit_data.seeking_venue = submit_form.seeking_venue.data
    edit_data.seeking_description = submit_form.seeking_description.data
    edit_data.image_link = submit_form.image_link.data
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  edit_venue = Venue.query.filter_by(id = venue_id).all()[0]
  venue={
    "id": edit_venue.id,
    "name": edit_venue.name,
    "genres": edit_venue.genres.split(","),
    "address": edit_venue.address,
    "city": edit_venue.city,
    "state": edit_venue.state,
    "phone": edit_venue.phone,
    "website": edit_venue.website,
    "facebook_link": edit_venue.facebook_link,
    "seeking_talent": edit_venue.seeking_talent,
    "seeking_description":  edit_venue.seeking_description,
    "image_link": edit_venue.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  form = VenueForm(
    name = venue["name"], genres = venue["genres"], address = venue["address"], city = venue["city"],
    state = venue["state"], phone = venue["phone"], website_link = venue["website"],
    facebook_link = venue["facebook_link"], seeking_talent = venue["seeking_talent"], 
    seeking_description = venue["seeking_description"], image_link = venue["image_link"]
  )
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    submit_form = VenueForm(request.form)
    edit_data = Venue.query.get(venue_id)
    edit_data.name = submit_form.name.data
    edit_data.genres = str(",").join(submit_form.genres.data)
    edit_data.address = submit_form.address.data
    edit_data.city = submit_form.city.data
    edit_data.state = submit_form.state.data
    edit_data.phone = submit_form.phone.data
    edit_data.website = submit_form.website_link.data
    edit_data.facebook_link = submit_form.facebook_link.data
    edit_data.seeking_talent = submit_form.seeking_talent.data
    edit_data.seeking_description = submit_form.seeking_description.data
    edit_data.image_link = submit_form.image_link.data
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Artist record in the db, instead
  try:
    form = ArtistForm(request.form)
    data = Artist(
      name = form.name.data, city = form.city.data, state = form.state.data, phone = form.phone.data, genres = '',
      image_link = form.image_link.data, facebook_link = form.facebook_link.data, website = form.website_link.data,
      seeking_description = form.seeking_description.data, seeking_venue = form.seeking_venue.data
    )
    for item in enumerate(form.genres.data):
      if item[0] != (len(form.genres.data) - 1):
        data.genres += item[1] + ', '
      else:
        data.genres += item[1]
  except:
    # on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    print(sys.exc_info())
  else:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    db.session.add(data)
    db.session.commit()
    db.session.close()
  # TODO: modify data to be the data object returned from db insertion

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows_list = db.session.query(Show).all()
  # Process the shows_list and construct the data
  data = []
  for show in enumerate(shows_list):
    venue = Venue.query.filter_by(id = show[1][1]).all()[0]
    artist = Artist.query.filter_by(id = show[1][0]).all()[0]
    data.append({
      "venue_id": show[1][1],
      "venue_name": venue.name if venue else None,
      "artist_id": show[1][0],
      "artist_name": artist.name if artist else None,
      "artist_image_link": artist.image_link if artist else None,
      "start_time": show[1][2]
    }) 
  # Close the session
  db.session.close()
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  # on successful db insert, flash success
  try:
    showInfo = {
      'artist_id': request.form.get('artist_id'),
      'venue_id': request.form.get('venue_id'),
      'start_time': request.form.get('start_time')
    }
    data = Show.insert().values(artist_id = showInfo["artist_id"], venue_id = showInfo["venue_id"], start_time = showInfo["start_time"])

  except:
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.')
  else:
    if isValid_DateTime(showInfo["start_time"]) and len(showInfo["venue_id"]) > 0 and len(showInfo["artist_id"]) > 0:
      venue_data = Venue.query.filter_by(id = showInfo["venue_id"]).all()
      artist_data = Artist.query.filter_by(id = showInfo["artist_id"]).all()
      if len(venue_data) == 0 or len(artist_data) == 0:
        flash('Artist ID or Venue ID does not exist in table, please check again')
      else:
        show_data = db.session.query(Show).filter_by(artist_id = showInfo["artist_id"], venue_id = showInfo["venue_id"]).all()
        if len(show_data) == 0:
          db.session.execute(data)
          db.session.commit()
          flash('Show was successfully listed!')
        else:
          flash('already exists!')
    else:
      if len(showInfo["venue_id"]) == 0 and len(showInfo["artist_id"]) == 0:
        flash('You must enter Artist ID and Venue ID')
      else:
        flash('Incorrect format, please enter the following format: YYYY-MM-DD HH:MM:SS')
    db.session.close()
  return render_template('pages/home.html')

# Function to errorhandler
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# Function to validate
# DateTime(YYYY-MM-DD HH:MM:SS)
def isValid_DateTime(str):
    # Regex to check valid DateTime
    # (YYYY-MM-DD HH:MM:SS)
    regex = "^([0-9]{4})-((01|02|03|04|05|06|07|08|09|10|11|12|" \
    "(?:J(anuary|u(ne|ly))|February|Ma(rch|y)|A(pril|ugust)" \
    "|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)|" \
    "(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|" \
    "SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)|(September|October|" \
    "November|December)|(jan|feb|mar|apr|may|jun|jul|aug|sep|" \
    "oct|nov|dec)|(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|" \
    "NOV|DEC)))|(january|february|march|april|may|june|july|" \
    "august|september|october|november|december))-([0-3][0-9])" \
    "\\s([0-1][0-9]|[2][0-3]):([0-5][0-9]):([0-5][0-9])$"
    # Compile the ReGex
    p = re.compile(regex)
    # If the string is empty
    # return false
    if (str == None):
        return False
 
    # Return if the string
    # matched the ReGex
    if(re.search(p, str)):
        return True
    else:
        return False

def commonDef(current_date, dataList, category = 'venue'):
  dataType = {
    'upcoming_shows': 0,
    'past_shows': 0,
    'past_shows_list':[],
    'upcoming_shows_list':[]
  }
  for item in dataList:
    date = dateutil.parser.parse(item[2])
    time_format = babel.dates.format_datetime(date, "medium", locale='en')
    artist_info = Artist.query.filter_by(id = item[0]).first()
    venue_info = Venue.query.filter_by(id = item[1]).first()
    show_info = {
      'start_time': item[2],
      'artist_image_link': artist_info.image_link if artist_info else None,
      'venue_image_link': venue_info.image_link if venue_info else None,
      'artist_name': artist_info.name if artist_info else None,
      'venue_name': venue_info.name if venue_info else None
    }
    if current_date < time_format:
      dataType['upcoming_shows'] += 1
      if category == 'venue':
        show_info['artist_id'] = item[0]
      else:
        show_info['venue_id'] = item[1]
      dataType['upcoming_shows_list'].append(show_info)
    else:
      dataType['past_shows'] += 1
      if category == 'venue':
        show_info['artist_id'] = item[0]
      else:
        show_info['venue_id'] = item[1]
      dataType['past_shows_list'].append(show_info)
  return dataType

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
