#!/usr/bin/env python3

import logical_port_pb2
import telemetry_top_pb2
import socket
import time

from influxdb import InfluxDBClient

from datetime import datetime

import pprint
pp = pprint.PrettyPrinter(indent=4)

INFLUX_DB_PORT = 8086
INFLUX_DB_IP = "172.31.40.72"
INFLUX_DB_NAME = "throughput"
ANALYTICS_PORT = 50001


def main():
    # connect to DB
    influx = InfluxDBClient(INFLUX_DB_IP, INFLUX_DB_PORT,
                            "", "", INFLUX_DB_NAME)
    server(influx)


def server(influx):
    # create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", ANALYTICS_PORT))

    while True:
        data = sock.recv(32000)

        # create TelemetryStream object and parse data
        stream = telemetry_top_pb2.TelemetryStream()
        stream.ParseFromString(data)

        measurements = []

        # convert extension into JuniperNetworks object
        juniper_networks = stream.enterprise.Extensions[
            telemetry_top_pb2.juniperNetworks]
        # convert extension into LogicalInterfaceExt object
        logical_interfaces = juniper_networks.Extensions[
            logical_port_pb2.jnprLogicalInterfaceExt]

        # iterate over logical interfaces
        for interface_info in logical_interfaces.interface_info:

            # split system id "<name>:<IP>"
            system_name = stream.system_id.split(":")[0]

            # create measurement for received bytes
            measurement = {
                "measurement": "throughput_in",
                "tags": {
                    "host": system_name,
                    "interface": interface_info.if_name,
                },
                "time": stream.timestamp,
                "fields": {
                    "value": interface_info.ingress_stats.if_octets
                }
            }
            measurements.append(measurement)

            # create measurement for sent bytes
            measurement = {
                "measurement": "throughput_out",
                "tags": {
                    "host": system_name,
                    "interface": interface_info.if_name,
                },
                "time": stream.timestamp,
                "fields": {
                    "value": interface_info.egress_stats.if_octets
                }
            }
            measurements.append(measurement)

            # create measurement for drops if it exist
            tail_drop = 0
            red_drop = 0
            for queue_info in interface_info.egress_queue_info:
                tail_drop += queue_info.tail_drop_packets
                red_drop += queue_info.red_drop_packets

            measurement = {
                "measurement": "tail_drop_packets",
                "tags": {
                    "host": system_name,
                    "interface": interface_info.if_name,
                },
                "time": stream.timestamp,
                "fields": {
                    "value": tail_drop
                }
            }
            measurements.append(measurement)

            measurement = {
                "measurement": "red_drop_packets",
                "tags": {
                    "host": system_name,
                    "interface": interface_info.if_name,
                },
                "time": stream.timestamp,
                "fields": {
                    "value": red_drop
                }
            }
            measurements.append(measurement)

        # write to DB and reset buffer
        influx.write_points(measurements, time_precision='ms')
        measurements = []

    sock.close()


if __name__ == "__main__":
    main()
