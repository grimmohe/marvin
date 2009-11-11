import os, time, string

class device:
    self.file = None
    self.cb_readevent = None

    def __init__(self, filename, cb_event):
        self.file = os.open(filename, os.O_RDWR | os.O_SYNC)
        self.cb_readevent = cb_event

    def read(self):
        data = os.read(self.file, 80)
        if len(data) > 0:
            self.cb_readevent(data)

    def write(self, data):
        os.write(self.file, data)
        os.lseek(self.file, 0, os.SEEK_END)

class cleaner:
    self.pos_x         = 20
    self.pos_y         = 20
    self.orientation   = 0
    self.radius        = 20
    self.speed         = 10 # 1/s

class room:
    self.height        = 400
    self.width         = 400

class simulator:
    self.sensor_right  = None
    self.sensor_left   = None
    self.sensor_front  = None
    self.engine        = None
    self.client        = cleaner()    # Unser Staubsaugerrepresentant
    self.room          = room()       # Die Spielwiese

    self.starttime     = None
    self.stoptime      = None         # Wann ist ads Hindernis erreicht?
    self.runit         = False

    def __init__(self):
        self.sensor_right  = device('/tmp/dev_right', self.cb_sensor_right)
        self.sensor_left   = device('/tmp/dev_left', self.cb_sensor_left)
        self.sensor_front  = device('/tmp/dev_front', self.cb_sensor_front)
        self.engine        = device('/tmp/dev_engine', self.cb_engine)

    def cb_sensor_right(self, data):
        time.sleep(0)

    def cb_sensor_left(self, data):
        time.sleep(0)

    def cb_sensor_front(self, data):
        time.sleep(0)

    def cb_engine(self, data):
        data = string.split(data, "=")

        if data[0] == "drive":
            if data[1] == "1": # berechne, wann das nächste Hinderniss erreicht ist
                self.starttime = time.clock()
            else:
                time.sleep(0) # welche Position haben wir bis jetzt erreicht?
        elif data[0] == "turn":
            self.client.orientation += string.atoi(data[1])
        elif data[0] == "shutdown":
            self.runit = False

    # Prüfen, ob Sensordaten zu senden sind
    def check(self):
        time.sleep(0)

    # Main loop
    def run(self):
        self.runit = True
        while self.runit:
            self.engine.read()
            self.check()
            time.sleep(0.001)





