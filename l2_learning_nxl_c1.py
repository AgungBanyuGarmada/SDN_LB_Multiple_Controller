from __future__ import division
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str, str_to_dpid
from pox.lib.util import str_to_bool
import time
import threading
import pika
import itertools
import json
import MySQLdb

log = core.getLogger()
switch_load=[]
switch_load_counter=False
controller_loads = 0
max_controller_loads = 0
failover_treshold = True
failover_counter = 0

# We don't want to flood immediately when a switch connects.
# Can be overriden on commandline.
_flood_delay = 0

class LearningSwitch (object):
  def __init__ (self, connection, transparent, channelRabbitmq):
    # Switch we'll be adding L2 learning switch capabilities to
    self.connection = connection
    self.transparent = transparent

    # Our table
    self.macToPort = {}

    # We want to hear PacketIn messages, so we listen
    # to the connection
    connection.addListeners(self)

    # We just use this to know when to log a helpful message
    self.hold_down_expired = _flood_delay == 0

    #log.debug("Initializing LearningSwitch, transparent=%s",
    #          str(self.transparent))
    self.channelRabbitmq = channelRabbitmq
    global switch_load_counter
    if not switch_load_counter:
      self.printit()
      switch_load_counter=True

  """
      Publish the load into the other's controller queue
      """

  def publish(self, message):
    self.channelRabbitmq.basic_publish(exchange='',
                                       routing_key='queue_2',
                                       body=message,
                                       properties=pika.BasicProperties(
                                           delivery_mode=2,  # make message persistent
                                           ))

  """
  Print out the Controller and switch loads
  """
  def printit(self):
    threading.Timer(5.0, self.printit).start()
    global max_controller_loads
    global controller_loads
    controller_loads = 0
    for item in switch_load:
      temp_load = item[1] / 5
      print "Switch " + item[0] + " : " + str(temp_load) + " pps"
      controller_loads += temp_load
      item[1] = 0
    if max_controller_loads < controller_loads: max_controller_loads=controller_loads
    print ""
    print "Controller Load = " + str(controller_loads) + " pps"
    print ""
    print "Max Controller Load = " + str(max_controller_loads) + " pps"
    print "--------------------------------------------------"
    print ""
    self.publish(str(controller_loads))

  def _handle_PacketIn (self, event):
    """
    Handle packet in messages from the switch to implement above algorithm.
    """
    counter=True
    for item in switch_load:
      if item[0] == dpid_to_str(event.dpid):
        counter =False
        item[1]+=1
    if counter:
      switch_load.append([dpid_to_str(event.dpid),1])
    # print dpid_to_str(event.dpid)

    packet = event.parsed

    def flood (message = None):
      """ Floods the packet """
      msg = of.ofp_packet_out()
      if time.time() - self.connection.connect_time >= _flood_delay:
        # Only flood if we've been connected for a little while...

        if self.hold_down_expired is False:
          # Oh yes it is!
          self.hold_down_expired = True
          log.info("%s: Flood hold-down expired -- flooding",
              dpid_to_str(event.dpid))

        if message is not None: log.debug(message)
        #log.debug("%i: flood %s -> %s", event.dpid,packet.src,packet.dst)
        # OFPP_FLOOD is optional; on some switches you may need to change
        # this to OFPP_ALL.
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
      else:
        pass
        #log.info("Holding down flood for %s", dpid_to_str(event.dpid))
      msg.data = event.ofp
      msg.in_port = event.port
      self.connection.send(msg)

    def drop (duration = None):
      """
      Drops this packet and optionally installs a flow to continue
      dropping similar ones for a while
      """
      if duration is not None:
        if not isinstance(duration, tuple):
          duration = (duration,duration)
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet)
        msg.idle_timeout = duration[0]
        msg.hard_timeout = duration[1]
        msg.buffer_id = event.ofp.buffer_id
        self.connection.send(msg)
      elif event.ofp.buffer_id is not None:
        msg = of.ofp_packet_out()
        msg.buffer_id = event.ofp.buffer_id
        msg.in_port = event.port
        self.connection.send(msg)

    self.macToPort[packet.src] = event.port # 1

    if not self.transparent: # 2
      if packet.type == packet.LLDP_TYPE or packet.dst.isBridgeFiltered():
        drop() # 2a
        return

    if packet.dst.is_multicast:
      flood() # 3a
    else:
      if packet.dst not in self.macToPort: # 4
        flood("Port for %s unknown -- flooding" % (packet.dst,)) # 4a
      else:
        port = self.macToPort[packet.dst]
        if port == event.port: # 5
          # 5a
          log.warning("Same port for packet from %s -> %s on %s.%s.  Drop."
              % (packet.src, packet.dst, dpid_to_str(event.dpid), port))
          drop(10)
          return
        # 6
        log.debug("installing flow for %s.%i -> %s.%i" %
                  (packet.src, event.port, packet.dst, port))
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet, event.port)
        msg.idle_timeout = 10
        msg.hard_timeout = 30
        msg.actions.append(of.ofp_action_output(port = port))
        msg.data = event.ofp # 6a
        self.connection.send(msg)


class l2_learning (object):
  db = None
  """
  Waits for OpenFlow switches to connect and makes them learning switches.
  """
  def __init__ (self, transparent, ignore = None):
    """
    Initialize

    See LearningSwitch for meaning of 'transparent'
    'ignore' is an optional list/set of DPIDs to ignore
    """
    core.openflow.addListeners(self)
    self.transparent = transparent
    self.ignore = set(ignore) if ignore else ()

    """
    Rabbitmq configuration
    """
    self.connectionRabbitmq = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    self.channelRabbitmq = self.connectionRabbitmq.channel()
    self.channelRabbitmq.queue_declare(queue='queue_2', durable=True)
    threading._start_new_thread(self.subscriber, ())

  def _handle_ConnectionUp (self, event):
    if event.dpid in self.ignore:
      log.debug("Ignoring connection %s" % (event.connection,))
      return
    log.debug("Connection %s" % (event.connection,))
    LearningSwitch(event.connection, self.transparent, self.channelRabbitmq)

  def _handle_ConnectionDown (self, event):
    for i in switch_load:
      if i[0] == dpid_to_str(event.dpid):
        switch_load.remove(i)
  """
  collection load from another controller
  """
  def subscriber(self):
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='queue_1', durable=True)

    channel_pub = connection.channel()
    channel_pub.queue_declare(queue='queue_3', durable=True)

    def callback(ch, method, properties, body):
      global failover_treshold
      global failover_counter
      if failover_treshold:
        threading._start_new_thread(self.controller_failover, (channel_pub,))
        failover_treshold = False
      else:
        failover_counter = 0

      print(" [x] Received %r" % body)
      controller_loads_2 = float(body)
      ch.basic_ack(delivery_tag=method.delivery_tag)
      if controller_loads > controller_loads_2 and controller_loads+controller_loads_2 > 300:
        p = ((controller_loads + controller_loads_2)/2) / controller_loads
        print "p = ", p
        if p < 0.7:
          print "Controller Overload need to migrate some switch"
          self.switches_selection(controller_loads_2,channel_pub)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(callback,queue='queue_1')

    channel.start_consuming()

  def switches_selection(self,c2, pub_conn):
    Cave=(controller_loads+c2/2)
    target = controller_loads-Cave

    dif = 0
    temp = [switch_load, 9999]

    for L in range(0, len(switch_load) + 1):
      for subset in itertools.combinations(switch_load, L):
        total = 0
        if subset.__len__()>0:
          for i in subset:
            total += i[1]
          # print total
          if total < target:
            dif = target - total
          else:
            dif = total - target
          if dif <= temp[1]:
            temp = [subset, dif]

    for i in temp[0]:
      a = json.dumps({"Controller_id": "poxController2",
                      "Switch_id": i[0]})

      pub_conn.basic_publish(exchange='',
                             routing_key='queue_3',
                             body=a,
                             properties=pika.BasicProperties(
                               delivery_mode=2,
                             ))
  def controller_failover(self, pub_conn):
    global failover_counter
    while failover_counter <= 6:
      time.sleep(1)
      failover_counter+=1

    self.connectdb()
    sql = ("Select s_name, c_name from sdn_link where c_name = 'poxController2'")
    cursor = self.db.cursor()
    cursor.execute(sql)
    list_switch = cursor.fetchall()
    for item in list_switch:
      a = json.dumps({"Controller_id": "poxController",
                      "Switch_id": item[0]})

      pub_conn.basic_publish(exchange='',
                             routing_key='queue_3',
                             body=a,
                             properties=pika.BasicProperties(
                               delivery_mode=2,
                             ))
      time.sleep(1)

  def connectdb(self):
    self.db = MySQLdb.connect("localhost", "root", "", "Skripsi")

  def disconnectdb(self):
    self.db.close()
    self.db = None


def launch (transparent=False, hold_down=_flood_delay, ignore = None):
  """
  Starts an L2 learning switch.
  """
  try:
    global _flood_delay
    _flood_delay = int(str(hold_down), 10)
    assert _flood_delay >= 0
  except:
    raise RuntimeError("Expected hold-down to be a number")

  if ignore:
    ignore = ignore.replace(',', ' ').split()
    ignore = set(str_to_dpid(dpid) for dpid in ignore)

  core.registerNew(l2_learning, str_to_bool(transparent), ignore)
