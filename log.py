from datetime import datetime
import time

def writeOnFile(file, msg):
    try:
        file_object = open(file, 'a')
        timestamp = time.time()
        date_time = datetime.fromtimestamp(timestamp)
        str_date_time = date_time.strftime("%d-%m-%Y, %H:%M:%S")
        file_object.write(f"[ {str_date_time} ] {msg}\n")
        file_object.close()
    except Exception as e:
        print("ERROR", e)
