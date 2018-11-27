db=MySQLdb.connect(host='localhost', user='piecia', passwd='piecia1', db='testDB')
c=db.cursor()
c.execute('SELECT * FROM numbers')
result=c.fetchall()
print(result)
#------------------------------------------------------------
#------------------------------------------------------------
app = Flask(__name__)
@app.route('/')
def hello_world():
    return 'hello, world'
#--------------------------------------------------------
#------------------------------------------
#SCRIPT BAZY
CREATE TABLE IF NOT EXISTS sensors(
    pressure SMALLINT,
    dampness TINYINT,
    temperature FLOAT(3,1),
    lightIntensity1 FLOAT(4,2),
    lightIntensity2 FLOAT(4,2),
    distance SMALLINT
)
ALTER TABLE sensors ADD COLUMN save_data DATE
#----------------------------------------------
#----------------------------------------------
"""
# Servo Control
import time
import wiringpi
 
# use 'GPIO naming'
wiringpi.wiringPiSetupGpio()

led1 = 16
led2 = 20
led3 = 21
# 0 - input, 1 - output, 2 other e.g.pwm
wiringpi.pinMode(led1,1)
wiringpi.digitalWrite(led1,1)
wiringpi.pinMode(led2,1)
wiringpi.digitalWrite(led2,1)
wiringpi.pinMode(led3,1)
wiringpi.digitalWrite(led3,1)
time.sleep(10)
wiringpi.digitalWrite(led1,0)
wiringpi.digitalWrite(led2,0)
wiringpi.digitalWrite(led3,0)


# set #18 to be a PWM output
wiringpi.pinMode(18, wiringpi.GPIO.PWM_OUTPUT)

# set the PWM mode to milliseconds stype
wiringpi.pwmSetMode(wiringpi.GPIO.PWM_MODE_MS)
 
# divide down clock
wiringpi.pwmSetClock(192)
wiringpi.pwmSetRange(2000)

delay_period = 0.01
wiringpi.pwmWrite(18, 0)

wiringpi.pwmWrite(18, 50)
time.sleep(delay_period)
wiringpi.pwmWrite(18,0)

while True:
        for pulse in range(50, 250, 1):
                wiringpi.pwmWrite(18, pulse)
                time.sleep(delay_period)
        for pulse in range(250, 50, -1):
                wiringpi.pwmWrite(18, pulse)
                time.sleep(delay_period)



# use 'GPIO naming'
servo = 12
wiringpi.wiringPiSetup()
wiringpi.pinMode(servo,12)
wiringpi.pwmWrite(servo,500)
time.sleep(1)
wiringpi.pwmWrite(servo,0)
"""

##-----------------------------------------------
##-------------------------------------------------
    if((now-prev_day) > datetime.timedelta(minutes=1)):
        formatted_date = prev_day.strftime('%Y-%m-%d %H:%M:%S')
        c.execute('DELETE FROM sensors WHERE save_data < %s' , (formatted_date,))
        prev_day = now