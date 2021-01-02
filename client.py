import requests
import getpass
import json
BASE = 'http://127.0.0.1:5000'


token = ''
def get_request(path, username=None, password=None):
    global token
    response = requests.get(BASE + path, auth=(username, password), headers={'x-access-tokens': token})
    if 'token' in response.json():
        token = response.json()['token']
    return response.json()

def post_request(path, data):
    response = requests.post(BASE + path, data, headers={'x-access-tokens': token})
    return response.json()


def put_request(path, data):
    response = requests.put(BASE + path, data, headers={'x-access-tokens': token})
    return response.json()


def delete_request(path):
    response = requests.delete(BASE + path, headers={'x-access-tokens': token})
    return response.json()




while True:
    operation = input('Operation[GET/POST/PUT/DELETE]: ')

    authorization = 'n'
    if operation.upper() == 'GET':
        authorization = input('Authorization[y/n]: ')

    username =''
    password = ''
    if authorization == 'y':
        username = input('Username:')
        password = getpass.getpass()
    path = input('Path: ')

    try:
        if operation.upper() == "GET":

            response = get_request(path, username=username, password=password)
            print(response)

        elif operation.upper() == "POST":
            fromCity = input('From city: ')
            toCity =  input('To city: ')
            arrivalDate = input('Arrival date and time (yyyy-mm-dd hh:mm): ')
            departureDate = input('Departure date and time (yyyy-mm-dd hh:mm): ')
            boeingInfo = input('Boeing info: ')
            passengerNum = input('Number of passengers(integer): ')
            if passengerNum:
                passengerNum = int(passengerNum)
            new_flight = {
                        'fromCity': fromCity,
                        'toCity': toCity,
                        'arrivalDate': arrivalDate,
                        'departureDate': departureDate,
                        'boeingInfo': boeingInfo,
                        'passengerNum': passengerNum
                        }

            response = post_request(path, new_flight)
            print(response)


        elif operation.upper() == "PUT":
            print('Enter properties thath you want to update: ')
            fromCity = input('From city: ')
            toCity =  input('To city: ')
            arrivalDate = input('Arrival date and time (yyyy-mm-dd hh:mm): ')
            departureDate = input('Departure date and time (yyyy-mm-dd hh:mm): ')
            boeingInfo = input('Boeing info: ')
            passengerNum = input('Number of passengers: ')
            if passengerNum:
                passengerNum = int(passengerNum)
            new_flight = {
                        'fromCity': fromCity,
                        'toCity': toCity,
                        'arrivalDate': arrivalDate,
                        'departureDate': departureDate,
                        'boeingInfo': boeingInfo,
                        'passengerNum': passengerNum
                        }

            response = put_request(path, new_flight)
            print(response)
        

        elif operation.upper() == 'DELETE':
            response = delete_request(path)
            print(response)
        
        else:
            print('error: Operation is not correct!')
    except:
        print('error: Given path is not found')


