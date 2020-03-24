#!/usr/bin/python

import sys
from argparse import ArgumentParser
from os.path import join, expanduser

from mininet.log import setLogLevel, info
from mn_wifi.link import wmediumd, adhoc
from mn_wifi.cli import CLI_wifi
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference

from read_robots import read_robots


def start_runner(setup_file, out_file):

    # clear any existing content from out_file
    with open(out_file, "w") as f:
        f.flush()

    # get total count of Wifi devices
    robots = read_robots(setup_file)

    "Create a network."
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    stations = list()
    for i, robot in enumerate(robots):
        station_name = "sta%d"%i # sta0
        position = robot.position_string()
        station_range = 100
        info(" station %s position %s range %d\n"%(station_name, position, station_range))
        station = net.addStation(station_name, position=position,
                                 range=station_range)
        stations.append(station)

    net.setPropagationModel(model="logDistance", exp=4)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Creating links\n")

    for i in range(len(robots)):
        station = stations[i]
        net.addLink(station, cls=adhoc, intf='sta%d-wlan0'%i, ssid='adhocNet',
                    mode='g', channel=5, ht_cap='HT40+')

    info("*** Starting network\n")
    net.build()

    info("\n*** Starting ROS2 nodes...\n")
    for i, robot in enumerate(robots):
        station = stations[i]
        robot_name = "r%d"%i
        role = robot.role
        cmd = "ros2 run testbed_nodes testbed_robot %s %s %s %s &"%(
                                robot_name, role, setup_file, out_file)
        info("*** Starting '%s'\n"%cmd)
        station.cmd(cmd)

    info("*** Running CLI\n")
    CLI_wifi(net)

    info("*** Stopping network\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')

    # args
    parser = ArgumentParser(description="Start Mininet swarm emulation")
    parser.add_argument("setup_file", type=str, help="Testbed setup file")
    parser.add_argument("out_file", type=str, help="Output file")
    args = parser.parse_args()

    start_runner(expanduser(args.setup_file), expanduser(args.out_file))

