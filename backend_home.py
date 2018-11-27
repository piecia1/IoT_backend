#!/usr/bin/python
import time
from flask import Flask,jsonify,json,abort
from flask import request,make_response
from flask_cors import CORS, cross_origin
import MySQLdb
import serial
import datetime
import RPi.GPIO as GPIO
import wiringpi
import hashlib, random
#------------------------------------------------------------------
#------------------------------------------------------------------
# Kolejność wysyłania danych
pres= 0
damp = 1
temp = 2
light1 = 3
light2 = 4
dist = 5

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.before_request
def option_autoreply():
    """ Always reply 200 on OPTIONS request """

    if request.method == 'OPTIONS':
        resp = app.make_default_options_response()

        headers = None
        if 'ACCESS_CONTROL_REQUEST_HEADERS' in request.headers:
            headers = request.headers['ACCESS_CONTROL_REQUEST_HEADERS']

        h = resp.headers

        # Allow the origin which made the XHR
        h['Access-Control-Allow-Origin'] = request.headers['Origin']
        # Allow the actual method
        h['Access-Control-Allow-Methods'] = request.headers['Access-Control-Request-Method']
        # Allow for 10 seconds
        h['Access-Control-Max-Age'] = "10"

        h['Access-Control-Allow-Credentials'] = "true"

        # We also keep current headers
        if headers is not None:
            h['Access-Control-Allow-Headers'] = headers

        return resp


@app.after_request
def set_allow_origin(resp):
    """ Set origin for GET, POST, PUT, DELETE requests """

    h = resp.headers

    # Allow crossdomain for other HTTP Verbs
    if request.method != 'OPTIONS' and 'Origin' in request.headers:
        h['Access-Control-Allow-Origin'] = request.headers['Origin']


    return resp




@app.route('/addUser', methods=['GET'])
@cross_origin(origin='*')
def addUser():
    #Sprawdzenie loginu i hasła
    auth = request.authorization
    if(not auth):
        return jsonify({'info' : 'Nie przesłałeś danych do logowania'})
    
    login, password = auth.username, auth.password
    if((not login) or  (not password)):
        return jsonify({'info':'Brak loginu lub hasła'})
    
    # Połączenia z baza danych
    db=MySQLdb.connect(host='localhost', user='piecia', passwd='piecia1', db='home')
    cur=db.cursor()
    
    #Sprawdzamy czy użytkownik istnieje w bazie
    check_login = checkUserByLogin(cur,login)
    if(check_login):
        return jsonify({'info' : 'Użytkownik istnieje już w bazie'})
    #sól
    salt = str(random.getrandbits(32))
    #token
    token = random.getrandbits(32)
    
    #hashowanie hasła
    db_password = password + salt
    h_password = hashlib.md5(db_password.encode())
    hash_password = h_password.hexdigest()
    
    #Dodanie użytkownika
    query = 'INSERT INTO home_user(name, user_password, salt, token) VALUES(%s,%s,%s,%s)'
    cur.execute(query, (login,hash_password,salt,token))
    db.commit()
    cur.close()
    db.close()
    
    return jsonify({'info' : 'dodano nowego użytkownika'})

@app.route('/checkUser', methods=['GET'])
@cross_origin(origin='*')
def checkUser():
    #Sprawdzenie loginu i hasła
    auth = request.authorization
    if(not auth):
        return jsonify({'info' : 'Nie przesłałeś danych do logowania'})
    
    login, password = auth.username, auth.password
    if((not login) or  (not password)):
        return jsonify({'info':'Brak loginu lub hasła'})
    
    # Połączenia z baza danych
    db=MySQLdb.connect(host='localhost', user='piecia', passwd='piecia1', db='home')
    cur=db.cursor()
    
    # Sprawdzenie loginu
    user = checkUserByLogin(cur, login)
    if( not user):
        return jsonify({'info' : 'Niepoprawny login'})
    
    #Przygotowanie hasła
    db_password = password + user[3]
    h_password = hashlib.md5(db_password.encode())
    hash_password = h_password.hexdigest()
    if(user[2] != hash_password):
        return jsonify({'info' : 'Niepoprawne hasło'})
    elif(user[2] == hash_password):
        #token
        token = random.getrandbits(32)
        query = 'UPDATE home_user SET token = %s WHERE name = %s'
        cur.execute(query, (token, user[1]))
        db.commit()
        cur.close()
        db.close()
        return jsonify({'token' : token})
    else:
        cur.close()
        db.close()
        return jsonify({'info' : 'Nieznany błąd'})

@app.route('/sensors', methods=['GET'])
@cross_origin(origin='*')
def sensors():
    auth = request.authorization
    if(not auth):
        return jsonify({'info' : 'Nie przesłałeś danych auth'})
    login = auth.username
    if(not login):
        return jsonify({'info' : 'Brak loginu'})
    try:
        token = int(request.headers.get('Authentication'))
    except (TypeError, ValueError):
        return jsonify({'info' : 'Niepoprawny typ danych Authentication'})
    # Połączenia z baza danych
    db=MySQLdb.connect(host='localhost', user='piecia', passwd='piecia1', db='home')
    cur=db.cursor()
    #Sprawdzenie poprawności danych
    checkUser = checkUserToken(cur,login,token)
    if(not checkUser):
        cur.close()
        db.close()
        return jsonify({'info' : 'Niepoprawny login lub token'})
    # Jeżeli wszystko oki zwróć dane
    query = 'SELECT * FROM sensors WHERE save_data=(SELECT MAX(save_data) FROM sensors)'
    cur.execute(query)
    data = cur.fetchone()
    cur.close()
    db.close()
    return jsonify({'pressure': data[0], 'dampness':data[1],'temperature':data[2],
                    'lightIntensity1':data[3],'lightIntensity2':data[4],'distance':data[5],
                    'date':data[6]})
    

@app.route('/sterr', methods=['PUT'])
@cross_origin(origin='*')
def sterr():
    auth = request.authorization
    if(not auth):
        return jsonify({'info' : 'Nie przesłałeś danych auth'})
    login = auth.username
    if(not login):
        return jsonify({'info' : 'Brak loginu'})
    try:
        token = int(request.headers.get('Authentication'))
    except (TypeError, ValueError):
        return jsonify({'info' : 'Niepoprawny typ danych Authentication'})
    # Połączenia z baza danych
    db=MySQLdb.connect(host='localhost', user='piecia', passwd='piecia1', db='home')
    cur=db.cursor()
    #Sprawdzenie poprawności danych
    checkUser = checkUserToken(cur,login,token)
    if(not checkUser):
        cur.close()
        db.close()
        return jsonify({'info' : 'Niepoprawny login lub token'})
    # Jeżeli wszystko oki zwróć dane
    data=request.get_json()
    # use 'GPIO naming'
    wiringpi.wiringPiSetupGpio()

    led1 = 16
    led2 = 20
    led3 = 21
    # 0 - input, 1 - output, 2 other e.g.pwm
    wiringpi.pinMode(led1,1)
    wiringpi.pinMode(led2,1)
    wiringpi.pinMode(led3,1)
    # silnik
    
    # set #18 to be a PWM output
    wiringpi.pinMode(18, wiringpi.GPIO.PWM_OUTPUT)
    # set the PWM mode to milliseconds stype
    wiringpi.pwmSetMode(wiringpi.GPIO.PWM_MODE_MS)
    # divide down clock
    wiringpi.pwmSetClock(384)
    wiringpi.pwmSetRange(1000)
    
    for key, value in data.items():
        if(key == "led1"):
            if(value == "true"):
                wiringpi.digitalWrite(led1,1)
            else:
                wiringpi.digitalWrite(led1,0)
        if(key == "led2"):
            if(value == "true"):
                wiringpi.digitalWrite(led2,1)
            else:
                wiringpi.digitalWrite(led2,0)
        if(key == "led3"):
            if(value == "true"):
                wiringpi.digitalWrite(led3,1)
            else:
                wiringpi.digitalWrite(led3,0)
        if(key=="servo"):
            value=int(value)
            wiringpi.pwmWrite(18, value)
    return jsonify({'info':'Piny ustawione'})

@app.route('/dateRange', methods=['GET'])
@cross_origin(origin='*')
def dateRange():
    auth = request.authorization
    if(not auth):
        return jsonify({'info' : 'Nie przesłałeś danych auth'})
    login = auth.username
    if(not login):
        return jsonify({'info' : 'Brak loginu'})
    try:
        token = int(request.headers.get('Authentication'))
    except (TypeError, ValueError):
        return jsonify({'info' : 'Niepoprawny typ danych Authentication'})
    # Połączenia z baza danych
    db=MySQLdb.connect(host='localhost', user='piecia', passwd='piecia1', db='home')
    cur=db.cursor()
    #Sprawdzenie poprawności danych
    checkUser = checkUserToken(cur,login,token)
    if(not checkUser):
        cur.close()
        db.close()
        return jsonify({'info' : 'Niepoprawny login lub token'})
    # Jeżeli wszystko oki zwróć dane
    params = request.args
    startTime, endTime = False, False 
    for key, value in params.items():
        if(key == "startTime"):
            try:
                startTime = datetime.datetime.strptime(value,"%a, %d %b %Y %H:%M:%S %Z")
            except ValueError:
                return jsonify({'info' : 'Niepoprawny format daty'})
        elif(key == "endTime"):
            try:
                endTime = datetime.datetime.strptime(value,"%a, %d %b %Y %H:%M:%S %Z")
            except ValueError:
                return jsonify({'info' : 'Niepoprawny format daty'})
    if((not startTime) and (not endTime)):
        query = 'select * from sensors'
        cur.execute(query)
        sensors_data = cur.fetchall()
    elif(startTime and (not endTime)):
        query = 'select * from sensors where save_data >= %s'
        cur.execute(query, (startTime,))
        sensors_data = cur.fetchall()
    elif((not startTime) and endTime):
        query = 'select * from sensors where save_data <= %s'
        cur.execute(query, (endTime,))
        sensors_data = cur.fetchall()
    else:
        query = 'select * from sensors where save_data >= %s AND save_data <= %s'
        cur.execute(query, (startTime, endTime))
        sensors_data = cur.fetchall()
    list_data=list()
    for data in sensors_data:
        list_data.append({'pressure': data[0], 'dampness':data[1],'temperature':data[2],
                    'lightIntensity1':data[3],'lightIntensity2':data[4],'distance':data[5],
                    'date':data[6]})
    return jsonify(list_data)

def checkUserByLogin(cur,login):
    login = login
    query = 'select * from home_user where name = %s'
    cur.execute(query, (login,))
    logged_user = cur.fetchone() 
    if(logged_user):
        return logged_user
    else:
        return False
    
def checkUser(cur,login, password):
    query = 'select * from home_user where name = %s AND password = %s'
    cur.execute(query, (login, password))
    logged_user = cur.fetchone() 
    if(logged_user):
        return logged_user
    else:
        return False

def checkUserToken(cur,login, token):
    query = 'select * from home_user where name = %s AND token = %s'
    cur.execute(query, (login, token))
    logged_user = cur.fetchone() 
    if(logged_user):
        return True
    else:
        return False

"""
prev_day = datetime.datetime.now()
while 1:
buf = list(map(float,ser.readline().split()))
now = datetime.datetime.now()
formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
c.execute()
#db.commit()
"""
