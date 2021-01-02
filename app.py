from flask import Flask, request
from flask_restful import Api, Resource, reqparse, marshal_with, fields, abort
from flask_sqlalchemy import SQLAlchemy
import json
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
import datetime 
from functools import wraps

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///databases/database.sqlite3'
app.config['SECRET_KEY'] = 'thisissecret'


db = SQLAlchemy(app)

class Admins(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), unique = True)
    password = db.Column(db.String(80))
    public_id = db.Column(db.String(50))




class Flights(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    fromCity = db.Column(db.String(20))
    toCity = db.Column(db.String(20))
    arrivalDate = db.Column(db.DateTime)
    departureDate = db.Column(db.DateTime)
    boeingInfo = db.Column(db.String(20))
    passengerNum = db.Column(db.Integer)



db.create_all()



resource_fields = {
    'id': fields.Integer,
    'fromCity': fields.String,
    'toCity': fields.String,
    'arrivalDate': fields.DateTime(dt_format='rfc822'),
    'departureDate': fields.DateTime(dt_format='rfc822'),
    'boeingInfo': fields.String,
    'passengerNum': fields.Integer
}


db.session.query(Admins).delete()
def fill_admin_database():
    with open('log_info.json', 'r') as readable:
        data = json.loads(readable.read())

    for user in data:
        hashed_password = generate_password_hash(user['password'], method='sha256')
        new_admin = Admins(username = user['login'], password = hashed_password, public_id = str(uuid.uuid4()))


        db.session.add(new_admin)
        db.session.commit()



fill_admin_database()


parser_post = reqparse.RequestParser()
parser_post.add_argument('fromCity', required = True, help ='City from which plane will take off should be inserted')
parser_post.add_argument('toCity', required = True, help ='City to which plane will land should be inserted')
parser_post.add_argument('arrivalDate',required = True, help ='Arrival date should be inserted')
parser_post.add_argument('departureDate', required = True, help ='Departure date should be inserted')
parser_post.add_argument('boeingInfo', required = True, help ='Boeing info should be inserted')
parser_post.add_argument('passengerNum', type=int, required = True, help ='Number of passengers should be inserted')



parser_put = reqparse.RequestParser()
parser_put.add_argument('fromCity')
parser_put.add_argument('toCity',)
parser_put.add_argument('arrivalDate')
parser_put.add_argument('departureDate')
parser_put.add_argument('boeingInfo')
parser_put.add_argument('passengerNum')


def abort_if_doesnt_exist(flight_id):
    flight = Flights.query.filter_by(id = flight_id).first()
    # print(flight) 
    if not flight:
        abort(404, message='Flight with given id is not found')


tokens = []


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']
        if not token:
            return {"message": "Token is missing!"}, 401
        
        if token not in tokens:
            return {"message": "token is invalid"}, 401
        return f(*args, **kwargs)
    return decorator





class Login(Resource):

    def get(self):
        auth = request.authorization

        if not auth or not auth.username or not auth.password:
            return {'message': "Could not verify"}, 401

        admin = Admins.query.filter_by(username = auth.username).first()

        if admin and check_password_hash(admin.password, auth.password):
            token = jwt.encode({'public_id': admin.public_id, 
            'exp': datetime.datetime.utcnow()+datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
       
            tokens.append(token)
            return {"token": token}

        return {"message": "Could not verify"} , 401





class EndSession(Resource):
    def get(self):
        if request.headers['x-access-tokens']:
            tokens.remove(request.headers['x-access-tokens'])
            return {"message": 'Successfully logged out!'}
        return {"message": 'You are already logged out!'}        





class AllFligths(Resource):
    @marshal_with(resource_fields)
    def get(self):
        result = Flights.query.all()
        return result



    @token_required
    @marshal_with(resource_fields)
    def post(self):
        
        args = parser_post.parse_args()
        
        new_flight = Flights(fromCity= args['fromCity'].capitalize(), toCity=args['toCity'].capitalize(),
        arrivalDate=datetime.datetime.strptime(args['arrivalDate'], '%Y-%m-%d %H:%M'),
        departureDate=datetime.datetime.strptime(args['departureDate'], '%Y-%m-%d %H:%M'),
        boeingInfo=args['boeingInfo'], passengerNum=args['passengerNum'])

        db.session.add(new_flight)
        db.session.commit()

        return new_flight




class ChosenFlights(Resource):
    @marshal_with(resource_fields)
    def get(self, fromCity, toCity):

        if fromCity == 'null' and toCity == 'null':
            return {'message': 'Bad request'}, 400

        fromCity = fromCity.capitalize()
        toCity  = toCity.capitalize()

        if fromCity != 'null' and toCity != 'null':
            result = Flights.query.filter_by(fromCity=fromCity, toCity=toCity).all()
        elif fromCity != 'null':
            result = Flights.query.filter_by(fromCity=fromCity).all()
        else:
            result = Flights.query.filter_by(toCity=toCity).all()
            

        if not result:
            abort (404, message="Flight with given paramaters is not found")

        return result



class ParticularFlight(Resource):
    @token_required
    @marshal_with(resource_fields)
    def put(self, flight_id):
        abort_if_doesnt_exist(flight_id)

        flight = Flights.query.filter_by(id = flight_id).first()

        args = parser_put.parse_args()

        for key, value in args.items():
            if value:
                setattr(flight, key, value)

        db.session.commit()
        return flight
        
    @token_required
    @marshal_with(resource_fields)
    def delete(self, flight_id):
        abort_if_doesnt_exist(flight_id)

        flight = Flights.query.filter_by(id = flight_id).first()
        db.session.delete(flight)
        db.session.commit()

        return flight


api.add_resource(Login, '/authentication_authorization')
api.add_resource(AllFligths, '/flights')
api.add_resource(ChosenFlights, '/flights/<string:fromCity>/<string:toCity>')
api.add_resource(ParticularFlight, '/flights/<int:flight_id>')
api.add_resource(EndSession, '/end_session')


if __name__ == '__main__':
    app.run(debug=True)

    