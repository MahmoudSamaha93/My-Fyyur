#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import datetime
from flask.json import jsonify
# from starter_code.forms import ArtistForm, ShowForm, VenueForm
import psycopg2
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from starter_code.forms import *
from starter_code.config import *
from flask_migrate import Migrate
from models import app, db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
moment = Moment(app)
db = SQLAlchemy(app)
db.init_app(app)


# TODO: connect to a local postgresql database
migrate = Migrate(app, db)


# -------------------------- Models imported from models.py file ------------#


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

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
  # Done
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[]

  areas = Venue.query.with_entities(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()

  for area in areas:
      data_venues = []
      venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()

      for venue in venues:
          upcoming_shows = db.session.query(Show).filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all()
          data_venues.append({
              'id': venue.id,
              'name': venue.name,
              'num_upcoming_shows': len(upcoming_shows)
          })

      data.append({
          'city': area.city,
          'state': area.state,
          'venues': data_venues
      })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # Done
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term = request.form.get('search_term')
  venues = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all()
  data = []
  for result in venues:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == result.id).filter(Show.start_time > datetime.now()).all()),
      })

  response={
    "count": len(venues),
    "data": data
    }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # Done
  # TODO: replace with real venue data from the venues table, using venue_id
  # Done

  venue=Venue.query.get(venue_id)
  shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).all()
  data=[]
  upcoming_shows = []

  for show in shows_query:
      if show.start_time > datetime.now():
          upcoming_shows.append({
              "artist_id": show.artist_id,
              "artist_name": show.Artist.name,
              "artist_image_link": show.Artist.image_link,
              "start_time": format_datetime(str(show.start_time))
          })

  past_shows = []

  for show in shows_query:
      if show.start_time < datetime.now():
          past_shows.append({
              "artist_id": show.artist_id,
              "artist_name": show.Artist.name,
              "artist_image_link": show.Artist.image_link,
              "start_time": format_datetime(str(show.start_time))

          })

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
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
  # TODO: modify data to be the data object returned from db insertion
  # Done
  form = VenueForm(request.form)
  
  #Create a venue object that will have the following fields (because they're the fields that do exist in the new_venue html unlike the model which has additional fields like seeking value)
  venue = Venue(
      name = form.name.data,
      city = form.city.data,
      state = form.state.data,
      genres= form.genres.data,
      address = form.address.data,
      phone = form.phone.data,
      image_link = form.image_link.data,
      facebook_link = form.facebook_link.data,
      website = form.website.data,
      seeking_talent = form.seeking_talent.data,
      seeking_description = form.seeking_description.data
  )
  try:
      db.session.add(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
  
  except:
      db.session.rollback()
      # on unsuccessful db insert, flash an error instead
      flash('An error occurred. Venue ' + request.form['name'] +  ' could not be listed.')
  
  finally:
      db.session.close()
  
  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # Done

  venue = Venue.query.get(venue_id)
  
  try:
      db.session.delete(venue)
      db.session.commit()

  except:
      db.session.rollback()
  
  finally:
      db.session.close()
  
  return 'Deleted venue  '+ venue.name +' succesfully'
 
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None


# Delete Venue
# -----------------------------------------------------------------

@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Artist.query.filter_by(id = venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
    
  return jsonify({ 'success': True })




#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = db.session.query(Artist).all()

  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # Done
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form.get('search_term')

  artists = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()

  data = []

  for result in artists:
    data.append({
    "id": result.id,
    "name": result.name,
    "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == result.id).filter(Show.start_time > datetime.now()).all())
    })

  response={
    "count": len(artists),
    "data": data
    }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  # Done

  artist = Artist.query.filter_by(id=artist_id).first()

  shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).all()

  upcoming_shows = []

  for show in shows_query:
      if show.start_time > datetime.now():
          upcoming_shows.append({
              "venue_id": show.venue_id,
              "venue_name": show.Venue.name,
              "venue_image_link": show.Venue.image_link,
              "start_time": format_datetime(str(show.start_time))
          })

  past_shows = []

  for show in shows_query:
      if show.start_time < datetime.now():
          past_shows.append({
              "venue_id": show.venue_id,
              "venue_name": show.Venue.name,
              "venue_image_link": show.Venue.image_link,
              "start_time": format_datetime(str(show.start_time))
          })

  data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  
  #Artist fields details from artist with ID
  artist = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
    }
  # TODO: populate form with fields from artist with ID <artist_id>
  # Done

  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # Done

  # artist record with ID <artist_id> using the new attributes

  form = ArtistForm(request.form)
  artist = Artist.query.filter_by(id=artist_id).first()
 
  try:
      artist.name = request.form['name']
      artist.genres = request.form['genres']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.facebook_link = form.facebook_link.data
      artist.image_link = request.form['image_link']
      artist.website = request.form['website']
      artist.seeking_venue = True if request.form['seeking_venue'] == 'Yes' else False
      artist.seeking_description = request.form['seeking_description']
      
      db.session.commit()
  
  except:
      db.session.rollback()

  finally:
      db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id).first()

  # Populate venue values
  venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }

  # TODO: populate form with values from venue with ID <venue_id>
  # Done

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # Done

  # venue record with ID <venue_id> using the new attributes

  form = VenueForm()
 
  venue = Venue.query.get(venue_id)

  try: 
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']
    venue.image_link = request.form['image_link']
    venue.website = request.form['website']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']
    
    db.session.commit()

  except: 
    db.session.rollback()

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
  # TODO: insert form data as a new Venue record in the db, instead
  # Done

  # TODO: modify data to be the data object returned from db insertion
  # Done

  form = ArtistForm(request.form)
  
  artist = Artist(
      name = form.name.data,
      city = form.city.data,
      state = form.state.data,
      phone = form.phone.data,
      genres = form.genres.data,
      facebook_link = form.facebook_link.data,
  )
  try:
      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success and display the name of the new artist
      flash('Artist ' + form.name.data + ' was successfully listed!')
 
  except:
        # on unsuccessful db insert, flash an error and display the name of the attempted new artist
      flash('An error occurred. Artist ' + form.name.data + 'could not be added')
  
  finally:
      db.session.close()

  return render_template('pages/home.html')


# Delete Artist
# -----------------------------------------------------------------

@app.route('/artists/<int:artist_id>', methods=['DELETE'])
def delete_todo(artist_id):
  try:
    Artist.query.filter_by(id = artist_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
    
  return jsonify({ 'success': True })


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  # Done

  #       num_shows should be aggregated based on number of upcoming shows per venue.
 
  data = []
  shows = Show.query.order_by(Show.start_time.desc()).all()
  
  for show in shows:
      data.append({
          "venue_id": show.venue_id,
          "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
          "artist_id": show.artist_id,
          "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
          "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
          "start_time": format_datetime(str(show.start_time))
      })

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
  # Done 

  form = ShowForm(request.form)

  show = Show(
      venue_id = form.venue_id.data,
      artist_id = form.artist_id.data,
      start_time = form.start_time.data
  )
  try:
      db.session.add(show)
      db.session.commit()
      # on successful db insert, flash success
      flash('Show was successfully listed!')

  except:
      db.session.rollback()
      # on unsuccessful db insert, flash an error instead
      flash('An error occurred. Show could not be listed.')

  finally:
      db.session.close()

  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

@app.errorhandler(401)
def unathorized(error):
    return render_template('errors/401.html'), 401

@app.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(422)
def not_processable(error):
    return render_template('errors/500.html'), 422

@app.errorhandler(405)
def invalid_method(error):
    return render_template('errors/500.html'), 405

@app.errorhandler(409)
def duplicate_resource(error):
    return render_template('errors/500.html'), 409


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

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
