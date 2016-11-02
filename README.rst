eQ-3/ELV MAX! Cube MQTT
=============================

Control your eQ-3/ELV MAX! Cube with MQTT


Installation:

    pip install maxcube-mqtt

Configuration:

Needs a json configuration file as follows (don't forget to change ip's and credentials ;-)):


    {
        "cube_host": "192.168.0.20",
        "cube_port": "62910",
        "mqtt_client_id": "maxcube",
        "mqtt_host": "192.168.0.210",
        "mqtt_port": "1883",
        "mqtt_user": "192.168.0.210",
        "mqtt_password": "1883",
        "mqtt_topic_prefix": "halti"
    }


Start:

    maxcube-mqtt config.json