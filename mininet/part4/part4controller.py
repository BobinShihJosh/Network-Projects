# Part 3 of UWCSE's Project 3
#
# based on Lab Final from UCSC's Networking Class
# which is based on of_tutorial by James McCauley

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, IPAddr6, EthAddr
import pox.lib.packet as pkt

from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.arp import arp

log = core.getLogger()

#statically allocate a routing table for hosts
#MACs used in only in part 4
IPS = {
  "h10" : ("10.0.1.10", '00:00:00:00:00:01'),
  "h20" : ("10.0.2.20", '00:00:00:00:00:02'),
  "h30" : ("10.0.3.30", '00:00:00:00:00:03'),
  "serv1" : ("10.0.4.10", '00:00:00:00:00:04'),
  "hnotrust" : ("172.16.10.100", '00:00:00:00:00:05'),
}

class Part4Controller (object):
  """
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    print (connection.dpid)
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # This binds our PacketIn event listener
    connection.addListeners(self)
    #use the dpid to figure out what switch is being created
    if (connection.dpid == 1):
      self.s1_setup()
    elif (connection.dpid == 2):
      self.s2_setup()
    elif (connection.dpid == 3):
      self.s3_setup()
    elif (connection.dpid == 21):
      self.cores21_setup()
    elif (connection.dpid == 31):
      self.dcs31_setup()
    else:
      print ("UNKNOWN SWITCH")
      exit(1)

  def flood_all(self):
    msg=of.ofp_flow_mod(priority=1)
    msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
    self.connection.send(msg)
  
    msg = of.ofp_flow_mod(priority=0)
    self.connection.send(msg)

  def s1_setup(self):
    #put switch 1 rules here
    self.flood_all()

  def s2_setup(self):
    #put switch 2 rules here
    self.flood_all()

  def s3_setup(self):
    #put switch 3 rules here
    self.flood_all()

  def cores21_setup(self):
    # hnotrust1 cannot send ICMP traffic to h10, h20, h30, or serv1
    msg = of.ofp_flow_mod(priority=10)
    msg.match.dl_type = 0x0800 # IPV4
    msg.match.nw_proto = 1 # ICMP
    msg.match.nw_src = IPS["hnotrust"][0]  # "172.16.10.100" 
    self.connection.send(msg)

    # hnotrust1 cannot send any IP traffic to serv1.
    msg = of.ofp_flow_mod(priority=9)
    msg.match.dl_type = 0x0800 # IPV4
    msg.match.nw_src = IPS["hnotrust"][0]  #"172.16.10.100"
    msg.match.nw_dst = IPS["serv1"][0] #"10.0.4.10"
    self.connection.send(msg)

  def dcs31_setup(self):
    #put datacenter switch rules here 
    self.flood_all()

  #used in part 4 to handle individual ARP packets
  #not needed for part 3 (USE RULES!)
  #causes the switch to output packet_in on out_port
  def resend_packet(self, packet_in, out_port):
    msg = of.ofp_packet_out()
    msg.data = packet_in
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)
    self.connection.send(msg)

  def _handle_PacketIn (self, event):
    """
    Packets not handled by the router rules will be
    forwarded to this method to be handled by the controller
    """

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.
    print ("Unhandled packet from " + str(self.connection.dpid) + ":" + packet.dump())

    if self.connection.dpid != 21:
      return

    if isinstance(packet.next, arp):
      actions = [of.ofp_action_dl_addr.set_dst(packet.src),
                       of.ofp_action_output(port=event.port)]
      match = of.ofp_match(dl_type=0x800,
                                 nw_dst=packet.next.protosrc)

      msg = of.ofp_flow_mod(priority=8,
                                  actions=actions,
                                  match=match)
      self.connection.send(msg)

      response = arp(hwsrc=packet.dst,
                       hwdst=packet.src,
                       protosrc=packet.next.protodst,
                       protodst=packet.next.protosrc,
                       opcode=2)
      e_msg = ethernet(type=ethernet.ARP_TYPE,
                         src=packet.dst,
                         dst=packet.src)
      e_msg.set_payload(response)
      self.resend_packet(e_msg, event.port)
    else:
      print ("Unhandled packet from " + str(self.connection.dpid) + ":" + packet.dump())

def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Part4Controller(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
