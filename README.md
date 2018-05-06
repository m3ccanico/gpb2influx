# gpb2influx

Receives JunOS analytics data (interface statistic encoded in Google Protocol Buffers), unpacks them, and writes them into InfluxDB.

## Install libraries

```bash
pip3 install influxdb protobuf
```

## Create protocol buffer parsers

Download the Google Protocol Buffer (GPB) specification (i.e. `.proto` files) for the JunOS device from Juniper: https://www.juniper.net/support/downloads/. It appears that not all devices have corresponding GPB specificatio files (Juniper calls them *JUNOS Telemetry Interface Data Model Files*). I've used the ones from the [MX204](https://www.juniper.net/support/downloads/?p=mx204).

The following command creates `logical_port.pb2.py` and `telemetry_top_pb2.py`. The two files are also included in the repo and don't need to be regenerated. The command is just here to document how to generate them:

```bash
apt install protobuf-compiler
protoc --proto_path=junos-telemetry-interface --python_out=. \
 junos-telemetry-interface/telemetry_top.proto \
 junos-telemetry-interface/logical_port.proto -I /usr/include
```

## Run

```bash
nohup gpb2influx.py &
```