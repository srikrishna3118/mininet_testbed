#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')

    info( '*** Add hosts\n')
    h1 = net.addHost('R1', cls=Host, ip='10.0.0.1', defaultRoute=None)
    h2 = net.addHost('R2', cls=Host, ip='10.0.0.2', defaultRoute=None)
    h3 = net.addHost('R3', cls=Host, ip='10.0.0.3', defaultRoute=None)
    h4 = net.addHost('R4', cls=Host, ip='10.0.0.4', defaultRoute=None)
    h5 = net.addHost('R5', cls=Host, ip='10.0.0.5', defaultRoute=None)

    info( '*** Add links\n')
    wifi_qos = {'bw':50,'delay':'2ms','loss':1,'max_queue_size':10,'jitter':'1'}
    net.addLink(s1, h1, cls=TCLink , **wifi_qos)
    net.addLink(s1, h2, cls=TCLink , **wifi_qos)
    net.addLink(s1, h3, cls=TCLink , **wifi_qos)
    net.addLink(s1, h4, cls=TCLink , **wifi_qos)
    net.addLink(s1, h5, cls=TCLink , **wifi_qos)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([])

    info( '*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

