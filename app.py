
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float, String
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import os

app = Flask(__name__)
#since sqlite is a file based database so we have to add the configuration or path
#we are putting our database file in the same folder as our runnning directory 
basedir = os.path.abspath(os.path.dirname(__file__))  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY']= 'super-secret'

#instantiated SQLAlchemy
db = SQLAlchemy(app)    #SQLAlchmey object
ma = Marshmallow(app)   
jwt = JWTManager(app)
#established an instance of Marshmallow using Marshmallow constructor

#scripts to create database, drop database and seed it.
#Using the decorator, we are making them commands on python CLI
@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database created!')

@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped!')

#to add test data to our database
@app.cli.command('db_seed')
def db_seed():
    mercury = planet(planet_name = 'Mercury',   
                    planet_type = 'Class D',
                    home_star = 'Sol',
                    mass = '3.258e23',
                    radius = '1516',
                    distance = '35.98e6')

    venus = planet(planet_name = 'Venus',   
                    planet_type = 'Class K',
                    home_star = 'Sol',
                    mass = '4.867e24',
                    radius = '3760',
                    distance = '67.24e6')

    earth = planet(planet_name = 'Earth',   
                    planet_type = 'Class M',
                    home_star = 'Sol',
                    mass = '5.972e24',
                    radius = '3959',
                    distance = '92.96e6')

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = user(first_name = 'Jack',   
                    last_name = 'Scott',
                    email = 'jackscott@gmail.com',
                    password = 'scott@123')

    db.session.add(test_user)
    db.session.commit()
    print('Database Seeded!')


@app.route("/")
def home():
    return "Hello, Flask!"


@app.route("/WOHOO")
def trying():
    return jsonify(message = "Welcome to a new endpoint!!!",hello="HAHA JUST TESTING!!!")


@app.route("/Parameters")
def param():
    name = request.args.get('name')
    age = request.args.get('age',type=int)
    if age < 18:
        return jsonify(message = 'Sorry,'+name+ 'You are not old enough! '), 401
    else:
        return jsonify(message="Welcome!!!"+name)

@app.route("/planets",methods=['GET'])
def planets():
    planets_list = planet.query.all()
    result = planets_schema.dump(planets_list)     #deserializing with Marshmallow
    return jsonify(result)

@app.route("/users", methods=['GET'])
def users():
    users_list = user.query.all()
    result = users_schema.dump(users_list)
    return jsonify(result)

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    test = user.query.filter_by(email=email).first()
    if test:
        return jsonify(message='That email already exists.'), 409
    else:
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password =request.form.get('password')
        #creating an object user
        new_user = user(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(message="User created successfully."), 201


@app.route('/login', methods=['POST'])
def login():
        email = request.form.get('email')
        password = request.form.get('password')
        test = user.query.filter_by(email=email, password=password).first()
        if test:
            access_token = create_access_token(identity=email)
            return jsonify(message="Logged in successfully!", access_token=access_token)
        else:
            return jsonify(message="Bad email or password."), 401

#CRUD ----> READ
@app.route('/planet_details/<int:planet_id>', methods=["GET"])
def planet_details(planet_id: int):
    planet_detail = planet.query.filter_by(planet_id=planet_id).first()
    if planet_detail:
        result = planet_schema.dump(planet_detail)
        return jsonify(result)
    else:
        return jsonify(message="That planet does not exist."), 404

#CRUD -----> CREATE
@app.route('/planet', methods=['POST'])
@jwt_required()
def add_planet():
    planet_name = request.form.get('planet_name')
    test = planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify(message="This planet already exists."), 409
    else:
        planet_type = request.form.get('planet_type')
        home_star = request.form.get('home_star')
        mass = request.form.get('mass', type = float)
        radius = request.form.get('radius', type=float)
        distance = request.form.get('distance', type = float)

        new_planet = planet(planet_name=planet_name,
                            planet_type=planet_type,
                            home_star=home_star,mass=mass,
                            radius=radius,
                            distance=distance)

        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message="Planet added successfully."), 201

#CRUD ------> UPDATE
@app.route("/planet", methods = ['PUT'])
@jwt_required()
def update():
    planet_id = request.form.get('planet_id', type = int)
    test = planet.query.filter_by(planet_id=planet_id).first()
    if test:
        test.planet_name = request.form.get('planet_name')
        test.planet_type = request.form.get('planet_type')
        test.home_star = request.form.get('home_star')
        test.mass = request.form.get('mass', type = float)
        test.radius = request.form.get('radius', type = float)
        test.distance = request.form.get('distance', type = float)
        
        db.session.commit()
        return jsonify(message="Planet updated successfully.")
    else:
        return jsonify(message="That planet does not exist."), 404

@app.route('/planet/<int:planet_id>',methods=['DELETE'])
@jwt_required
def delete_planet(planet_id: int):
    test = planet.query.filter_by(planet_id = planet_id).first()
    if test:
        db.session.delete(test)
        db.session.commit()
        return jsonify(message='Planet deleted successfully.')
    else:
        return jsonify(message='That planet does not exist.')

#database modeling
class user(db.Model):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key = True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique = True)
    password = Column(String)

class planet(db.Model):
    __tablename__ = 'Planets'
    planet_id = Column(Integer, primary_key = True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Integer)
    radius = Column(Integer)
    distance = Column(Integer)


class planetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id','planet_name','planet_type','home_star','mass','radius','distance')

class userSchema(ma.Schema):
    #creating inner class
    class Meta:
        #fields to expose
        fields = ('id','first_name','last_name','email','password')
 
user_schema = userSchema()               #to return only one value
users_schema = userSchema(many = True)   #to return multiple records

planet_schema = planetSchema()
planets_schema = planetSchema(many = True)


if __name__ == "__main__":
    app.run(debug=True)