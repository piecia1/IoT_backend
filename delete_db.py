import MySQLdb
import datetime
# Połączenia z baza danych
db=MySQLdb.connect(host='localhost', user='piecia', passwd='piecia1', db='home')
c=db.cursor()

time_to_delete = datetime.datetime.now() - datetime.timedelta(hours = 1) 
formatted_date = time_to_delete.strftime('%Y-%m-%d %H:%M:%S')
c.execute('DELETE FROM sensors WHERE save_data < %s' , (formatted_date,)) 
db.commit()
