import os
from datetime import datetime

from flask import Flask, redirect, render_template, request, send_from_directory, url_for, jsonify
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__, static_folder='static')
app.config['WTF_CSRF_ENABLED'] = False
csrf = CSRFProtect(app)

# WEBSITE_HOSTNAME exists only in production environment
if 'WEBSITE_HOSTNAME' not in os.environ:
    # local development, where we'll use environment variables
    print("Loading config.development and environment variables from .env file.")
    app.config.from_object('azureproject.development')
else:
    # production
    print("Loading config.production.")
    app.config.from_object('azureproject.production')

app.config.update(
    SQLALCHEMY_DATABASE_URI=app.config.get('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Initialize the database connection
db = SQLAlchemy(app)

# Enable Flask-Migrate commands "flask db init/migrate/upgrade" to work
migrate = Migrate(app, db)

# The import must be done after db initialization due to circular import issue
from models import Restaurant, Review, PixelCount

@app.route('/', methods=['GET'])
def index():
    print('Request for index page received')
    restaurants = Restaurant.query.all()
    return render_template('index.html', pixel_counts=PixelCount.query.all())

@app.route('/<int:id>', methods=['GET'])
def details(id):
    restaurant = Restaurant.query.where(Restaurant.id == id).first()
    reviews = Review.query.where(Review.restaurant == id)
    return render_template('details.html', restaurant=restaurant, reviews=reviews)

@app.route('/create', methods=['GET'])
def create_restaurant():
    print('Request for add restaurant page received')
    return render_template('create_restaurant.html')

@app.route('/add', methods=['POST'])
@csrf.exempt
def add_restaurant():
    # Si el cliente envía JSON, lo tratamos como API
    if request.is_json:
        data = request.get_json()
        # aceptamos tanto {"name":…} como {"restaurant_name":…}
        name           = data.get("restaurant_name") or data.get("name")
        street_address = data.get("street_address")
        description    = data.get("description")
        if not (name and street_address and description):
            return jsonify({"error":"faltan campos"}), 400

        restaurant = Restaurant(
            name           = name,
            street_address = street_address,
            description    = description
        )
        db.session.add(restaurant)
        db.session.commit()
        return jsonify({
            "id": restaurant.id,
            "name": restaurant.name,
            "street_address": restaurant.street_address,
            "description": restaurant.description
        }), 201

    # Si no es JSON, mantenemos el comportamiento de formulario HTML
    try:
        name           = request.values["restaurant_name"]
        street_address = request.values["street_address"]
        description    = request.values["description"]
    except KeyError:
        return render_template('create_restaurant.html', error_message="Debe incluir nombre, dirección y descripción"), 400

    restaurant = Restaurant(
        name           = name,
        street_address = street_address,
        description    = description
    )
    db.session.add(restaurant)
    db.session.commit()
    return redirect(url_for('details', id=restaurant.id))

@app.route('/review/<int:id>', methods=['POST'])
@csrf.exempt
def add_review(id):
    try:
        user_name = request.values.get('user_name')
        rating = request.values.get('rating')
        review_text = request.values.get('review_text')
    except (KeyError):
        #Redisplay the question voting form.
        return render_template('add_review.html', {
            'error_message': "Error adding review",
        })
    else:
        review = Review()
        review.restaurant = id
        review.review_date = datetime.now()
        review.user_name = user_name
        review.rating = int(rating)
        review.review_text = review_text
        db.session.add(review)
        db.session.commit()

    return redirect(url_for('details', id=id))

@app.context_processor
def utility_processor():
    def star_rating(id):
        reviews = Review.query.where(Review.restaurant == id)

        ratings = []
        review_count = 0
        for review in reviews:
            ratings += [review.rating]
            review_count += 1

        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        stars_percent = round((avg_rating / 5.0) * 100) if review_count > 0 else 0
        return {'avg_rating': avg_rating, 'review_count': review_count, 'stars_percent': stars_percent}

    return dict(star_rating=star_rating)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

#Método post para recibir los datos de pixelcount
@app.route("/add_pixel", methods=["POST"])
@csrf.exempt
def add_pixel_count():
    if not request.is_json:
        return jsonify({"error": "Formato no válido, se esperaba JSON."}), 400

    data = request.get_json()

    try: #Buscamos todos los campos necesarios
        usuario = data["usuario"]
        timestamp = datetime.fromisoformat(data["timestamp"])
        fichero = data["fichero"]
        pixeles = data["pixeles"]
    except KeyError as e: # Si falta alguno de los campos, devolvemos un error
        return jsonify({"error": f"Falta el campo {str(e)}"}), 400

    nuevo_pixel = PixelCount(#Realizamos el insert en la base de datos
        usuario=usuario,
        timestamp=timestamp,
        fichero=fichero,
        pixeles=pixeles
    )

    db.session.add(nuevo_pixel)
    db.session.commit()

    return jsonify({"id": nuevo_pixel.id}), 201

#Método para eliminar un pixelcount
@app.route('/eliminar/<int:id>', methods=['POST'])
@csrf.exempt
def eliminar_pixel(id):
    pixel = PixelCount.query.get_or_404(id)#Buscamos el pixelcount por id
    db.session.delete(pixel)#Eliminamos el pixelcount
    db.session.commit()
    return redirect(url_for('index'))

#Método para listar todos los pixelcounts
@app.route('/pixelcounts', methods=['GET'])
def list_pixel_counts():
    pixel_counts = PixelCount.query.all()#Obtenemos todos los pixelcounts
    return jsonify([{
        "id": p.id,
        "usuario": p.usuario,
        "timestamp": p.timestamp.isoformat(),
        "fichero": p.fichero,
        "pixeles": p.pixeles
    } for p in pixel_counts])

#Main method para ejecutar la app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
