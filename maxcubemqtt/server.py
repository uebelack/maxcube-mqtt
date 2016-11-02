import socket
import sys
import time
import traceback
import Queue
import paho.mqtt.client as mqtt
from threading import Thread
from threading import Timer
from maxcube.connection import MaxCubeConnection
from maxcube.cube import MaxCube


class MaxcubeMqttServer:
    config = None
    cube = None
    mqtt_connected = False
    mqtt_client = None
    status = {}
    device_mapping = {}
    cube_queue = Queue.Queue()
    cube_worker = None
    cube_timer = None

    def __init__(self, config):
        self.config = config
        self.cube_worker = Thread(target=self.cube_work)
        self.cube_worker.setDaemon(True)
        self.cube_worker.start()

    def verbose(self, message):
        if not self.config or 'verbose' not in self.config or self.config['verbose']:
            sys.stdout.write('VERBOSE: ' + message + '\n')
            sys.stdout.flush()

    def error(self, message):
        sys.stderr.write('ERROR: ' + message + '\n')
        sys.stderr.flush()

    def mqtt_connect(self):
        if self.mqtt_broker_reachable():
            self.verbose('Connecting to ' + self.config['mqtt_host'] + ':' + self.config['mqtt_port'])
            self.mqtt_client = mqtt.Client(self.config['mqtt_client_id'])
            if 'mqtt_user' in self.config and 'mqtt_password' in self.config:
                self.mqtt_client.username_pw_set(self.config['mqtt_user'], self.config['mqtt_password'])

            self.mqtt_client.on_connect = self.mqtt_on_connect
            self.mqtt_client.on_disconnect = self.mqtt_on_disconnect
            self.mqtt_client.on_message = self.mqtt_on_message

            try:
                self.mqtt_client.connect(self.config['mqtt_host'], int(self.config['mqtt_port']), 10)
                self.mqtt_client.subscribe(self.config['mqtt_topic_prefix'] + '/#')
                self.mqtt_client.loop_forever()
            except:
                self.error(traceback.format_exc())
                self.mqtt_client = None
        else:
            self.error(self.config['mqtt_host'] + ':' + self.config['mqtt_port'] + ' not reachable!')

    def mqtt_on_connect(self, mqtt_client, userdata, flags, rc):
        self.mqtt_connected = True
        self.verbose('...mqtt_connected!')
        self.cube_queue.put(Thread(target=self.cube_connect))

    def mqtt_on_disconnect(self, mqtt_client, userdata, rc):
        self.mqtt_connected = False
        self.verbose('Diconnected! will reconnect! ...')
        if rc is 0:
            self.mqtt_connect()
        else:
            time.sleep(5)
            while not self.mqtt_broker_reachable():
                time.sleep(10)
            self.mqtt_client.reconnect()

    def mqtt_on_message(self, client, userdata, message):
        self.verbose(message.topic)
        if self.cube and message.topic in self.device_mapping:
            self.cube_queue.put(Thread(target=self.cube.set_target_temperature,
                                       args=(self.device_mapping[message.topic], float(str(message.payload)))))

    def mqtt_broker_reachable(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        try:
            s.connect((self.config['mqtt_host'], int(self.config['mqtt_port'])))
            s.close()
            return True
        except socket.error:
            return False

    def cube_work(self):
        while True:
            if not self.cube_queue.empty():
                job = self.cube_queue.get()
                job.start()
                job.join()
                self.cube_queue.task_done()
            time.sleep(0.5)

    def cube_connect(self):
        self.cube = MaxCube(MaxCubeConnection(self.config['cube_host'], int(self.config['cube_port'])))
        self.device_mapping = {}
        for device in self.cube.devices:
            topic = self.config['mqtt_topic_prefix'] + '/' + device.name + '/target_temperature/set'
            self.device_mapping[topic] = device
        if self.cube_timer:
            self.cube_timer.cancel()

        self.cube_timer = Timer(300, self.update_cube())

    def update_cube(self):
        self.cube.update()
        self.publish_status()

    def publish_status(self):
        for device in self.cube.devices:
            topic_prefix = self.config['mqtt_topic_prefix'] + '/' + device.name

            topic = topic_prefix + '/actual_temperature'
            if device.actual_temperature and (topic not in self.status or self.status[topic] != device.actual_temperature):
                self.mqtt_client.publish(topic, str(device.actual_temperature), 0, True)
                self.status[topic] = device.actual_temperature

            topic = topic_prefix + '/target_temperature'
            if topic not in self.status or self.status[topic] != device.target_temperature:
                self.mqtt_client.publish(topic, str(device.target_temperature), 0, True)
                self.status[topic] = device.target_temperature

    def start(self):
        self.mqtt_connect()