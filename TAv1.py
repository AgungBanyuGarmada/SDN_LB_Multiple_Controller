from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host
from mininet.node import OVSKernelSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf


def MyNetwork():
    net= Mininet(topo=None,build=False , ipBase='10.0.0.0/8' , link=TCLink, host=CPULimitedHost)


    info("****Adding Controller1")
    print ""


    c1 = net.addController(name='poxController' ,
                           controller=RemoteController ,
                           ip='0.0.0.0' ,
                           port=6633)
    info("****Adding Second Controller")
    print ""
    c2 = net.addController(name='poxController2',
                           controller=RemoteController ,
                           ip='0.0.0.0' ,
                           port=6634)


    info('****Now Adding Two Switches')
    print ""

    switch1 = net.addSwitch('switch1')
    switch2 = net.addSwitch('switch2')
    switch3 = net.addSwitch('switch3')
    switch4 = net.addSwitch('switch4')
    switch5 = net.addSwitch('switch5')
    switch6 = net.addSwitch('switch6')
    switch7 = net.addSwitch('switch7')
    switch8 = net.addSwitch('switch8')


    host1=net.addHost('h1', ip='10.0.0.1/8', cpu=0.1)
    host2=net.addHost('h2', ip='10.0.0.2/8', cpu=0.1)
    host3=net.addHost('h3', ip='10.0.0.3/8', cpu=0.1)
    host4=net.addHost('h4', ip='10.0.0.4/8', cpu=0.1)
    host5=net.addHost('h5', ip='10.0.0.5/8', cpu=0.1)
    host6=net.addHost('h6', ip='10.0.0.6/8', cpu=0.1)
    host7=net.addHost('h7', ip='10.0.0.7/8', cpu=0.1)
    host8=net.addHost('h8', ip='10.0.0.8/8', cpu=0.1)


    net.addLink(host1, switch1, bw=100,max_queue_size=5000, use_htb=True)
    net.addLink(host2, switch2, bw=100,max_queue_size=5000, use_htb=True)
    net.addLink(host3, switch3, bw=100,max_queue_size=5000, use_htb=True)
    net.addLink(host4, switch4, bw=100,max_queue_size=5000, use_htb=True)
    net.addLink(host5, switch5, bw=100,max_queue_size=5000, use_htb=True)
    net.addLink(host6, switch6, bw=100,max_queue_size=5000, use_htb=True)
    net.addLink(host7, switch7, bw=100,max_queue_size=5000, use_htb=True)
    net.addLink(host8, switch8, bw=100,max_queue_size=5000, use_htb=True)


    net.addLink(switch1, switch2)
    net.addLink(switch2, switch3)
    net.addLink(switch3, switch4)
    net.addLink(switch4, switch5)
    # net.addLink(switch5, switch1)


    # net.addLink(switch4, switch1)


    net.addLink(switch5, switch6)
    net.addLink(switch6, switch7)
    net.addLink(switch7, switch8)
    # net.addLink(switch8, switch1)


    net.build()


    for controller in net.controllers:
        controller.start()


    net.get('switch1').start([c1,c2])
    net.get('switch2').start([c1,c2])
    net.get('switch3').start([c1,c2])
    net.get('switch4').start([c1,c2])
    net.get('switch5').start([c1,c2])
    net.get('switch6').start([c1,c2])
    net.get('switch7').start([c1,c2])
    net.get('switch8').start([c1,c2])

    # net.get('switch1').stop()
    # net.get('switch2').stop()
    # net.get('switch3').stop()
    # net.get('switch4').stop()
    # net.get('switch5').stop()
    # net.get('switch6').stop()
    # net.get('switch7').stop()
    # net.get('switch8').stop()


    # net.get('switch1').start([c1])
    # net.get('switch2').start([c1])
    # net.get('switch3').start([c1])
    # net.get('switch4').start([c1])
    # net.get('switch5').start([c2])
    # net.get('switch6').start([c2])
    # net.get('switch7').start([c2])
    # net.get('switch8').start([c2])

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    MyNetwork()