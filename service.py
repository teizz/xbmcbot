#!/usr/bin/python
import time, os, sys, re
import socket, ssl, json
from threading import Thread

import xbmc, xbmcaddon

__addon_name__ = 'XBMCBot'
__id__ = 'script.service.xbmcbot'
__author__ = 'Mattijs'
__platform__ = 'ALL'
__version__ = '0.7.1'

class IRCClient(Thread):

  # some regexes for parsing messages from irc server
  ping_re = re.compile('^PING (?P<message>.*)')
  error_re = re.compile('^ERROR (?P<message>.*)')
  pong_re = re.compile(':(?P<src>.*?)\s+?PONG\s+.*?:(?P<message>[^\n\r]+)')
  privmsg_re = re.compile(':(?P<src>.*?!\S+)\s+?PRIVMSG\s+[^#][^:]+:(?P<message>[^\n\r]+)')
  code_re = re.compile(':(?P<src>.*?)\s+(?P<message>\d+)\s+?.*')

  # not used for now
  nick_change_re = re.compile(':(?P<old_nick>.*?)!\S+\s+?NICK\s+:\s*(?P<new_nick>[-\w]+)')
  chanmsg_re = re.compile(':(?P<nick>.*?)!\S+\s+?PRIVMSG\s+(?P<channel>#+[-\w]+)\s+:(?P<message>[^\n\r]+)')
  part_re = re.compile(':(?P<nick>.*?)!\S+\s+?PART\s+(?P<channel>#+[-\w]+)')
  join_re = re.compile(':(?P<nick>.*?)!\S+\s+?JOIN\s+:\s*(?P<channel>#+[-\w]+)')
  quit_re = re.compile(':(?P<nick>.*?)!\S+\s+?QUIT\s+.*')

  def __init__(self, nick, auth, name):
    Thread.__init__(self)
    self.sock=socket.socket()
    self.writebuffer=list()
    self.readbuffer=""
    self.heartbeat={'last':time.time(),'recv':time.time()}
    self.commands=list()
    self.eventlog=list()
    self.admins=set()
    self.debug=False
    self.running=False
    
    self.nick=nick
    self.auth=auth
    self.name=name

  def connect(self,host,port,doSSL=False,ipv6=False):
    if socket.has_ipv6 and ipv6: self.sock=socket.socket(socket.AF_INET6)
    else: self.sock=socket.socket(socket.AF_INET)
    if doSSL: self.sock=ssl.wrap_socket(self.sock)
    try:
      self.sock.connect((host,port))
      self.writebuffer.append("USER %s 8 * :%s" % (self.nick, self.name))
      self.writebuffer.append("NICK %s" % self.nick)
      return self.flush()
    except: return False
    return True

  def registerWithServer(self):
    self.writebuffer.append("USER %s 8 * :%s" % (self.nick, self.name))
    self.writebuffer.append("NICK %s" % self.nick)
    return self.flush()

  def gracefullShutdown(self):
    self.log("Attempting a gracefull shutdown of IRC Thread")
    if self.sendQuit(): return 1
    elif self.disconnect(): return 2
    return 0

  def sendQuit(self, msg="Shutting down."):
    self.writebuffer.append("QUIT :%s" % msg)
    return self.flush()

  # try to disconnect the socket
  def disconnect(self):
    self.stop()
    try: self.sock.close()
    except: return False
    return True

  def sendPing(self):
    self.writebuffer.append("PING :%s" % self.nick)
    if self.flush():
      self.setPulse(True) # sending was successful
      return True
    return False

  def getPulse(self, soft=360, hard=420, interval=20):
    now=time.time()
    last=self.heartbeat['last']
    hard+=self.heartbeat['recv']
    soft+=self.heartbeat['recv']

    # don't check if check was done less than $interval ago
    if now<last+interval: return True
    # if the last received message was longer ago than the hard limit, something is wrong
    if now>hard: return False
    # if the last received message is longer ago than the soft limit, make an effort
    if now>soft: return self.sendPing()
    # everything is within bounds, nothing to see here move along
    return self.setPulse(True)

  def setPulse(self, onlySent=False):
    if not onlySent: self.heartbeat['recv']=time.time()
    self.heartbeat['last']=time.time()
    return True

  def registerCommand(self, name):
    try:
      m=__import__("commands."+name).__dict__[name]
      reload(m)
      c=m.Command(name, self)
      self.commands.append(c)
    except ImportError:
      return False
    return True

  def unregisterCommand(self, name):
    for c in self.commands:
      if c.getName()==name:
        self.commands.remove(c)
        if "commands"+name in sys.modules:
          del sys.modules['commands'+name]
        return True
    return False
  
  def getCommands(self):
    return self.commands

  def doAuth(self, auth):
    if self.auth == auth: return True
    return False

  def setDebug(self, debug):
    self.debug=debug

  def log(self, message):
    tag='XBMCBot.EVENT'
    logline="%d %s:: %s" % (int(time.time()),tag,message)
    if not tag in message: self.eventlog.append(logline)
    if self.debug: xbmc.log(logline)

  def stop(self):
    self.running=False
    return True

  def run(self):
    self.running=True
    # keep this loop going until an external call is made to stop it
    while self.running:
      xbmc.sleep(100) # just in case this thread goes haywire, no need to run off like that.
      
      # try and fetch some data from the open socket, continue if nothing is there
      try:
        self.sock.settimeout(0.1)
        self.readbuffer+=self.sock.recv(1500) #receive 1500 bytes
      except: pass
      
      # separate full lines from the readbuffer for processing, leave any incomplete lines in the readbuffer
      flines=self.readbuffer.split("\n") #build array of seperate lines
      self.readbuffer=flines.pop() #return incomplete line to buffer if any
      
      # process full lines from the readbuffer
      for rawline in flines: #proceed to process full lines
        # prepare the line and log it when in debug mode
        line=rawline.strip() #remove any white spaces
        self.log(">"+line)
        
        # since there was an incoming message, the connection is alive
        self.setPulse()
        
        # server sends numerical code
        if self.code_re.match(line):
          code=self.code_re.match(line).groupdict()['message']
          if code.isdigit():
            code=int(code)
            if code==1: self.log("Server accepted connection")
            if code==376 or code==422: self.log("End of MOTD reached")
            if code==433:
              self.log("Nick already in use")
              self.nick+="_"
              self.registerWithServer()
            
        # should match when the server hits us with an error
        if self.error_re.match(line):
          self.log("Server sent hard error, closing connection")
          self.stop()
          
        # server responded to a ping request made by this client
        if self.pong_re.match(line):
          reply=self.pong_re.match(line).groupdict()
          self.log("PONG received from %s with payload %s" % (reply['src'],reply['message']))
          
        # the server requested a ping response with a specific payload to test if the connection is still open.
        if self.ping_re.match(line):
          reply=self.ping_re.match(line).groupdict()
          self.writebuffer.append("PONG %s" % reply['message'])
          
        # a private message has been received and comes with a reply['nick'] sender and reply['message'] content.
        if self.privmsg_re.match(line):
          reply=self.privmsg_re.match(line).groupdict()
          for c in self.commands:
            c.parseline(reply)
         
      if not self.flush(): self.disconnect()

  def flush(self):
    # empty the writebuffer to the server, any data not sent is retained in the writebuffer. log anything when in debug mode.
    while self.writebuffer:
      try:
        self.sock.settimeout(10)
        self.sock.send(self.writebuffer[0]+"\r\n")
        self.log("<"+self.writebuffer.pop(0))
      except: return False
    return True
  
  def sendPrivateReply(self, dst, msg, notice=False):
    dst=dst.split("!")[0]
    if notice: self.writebuffer.append("NOTICE %s :%s" % (dst,msg))
    else: self.writebuffer.append("PRIVMSG %s :%s" % (dst,msg))

  # send a broadcast to all registred admins
  def sendAllReply(self, msg, notice=False):
    for dst in self.admins:
      dst=dst.split("!")[0]
      if notice: self.writebuffer.append("NOTICE %s :%s" % (dst,msg))
      else: self.writebuffer.append("PRIVMSG %s :%s" % (dst,msg))

  def sendRaw(self,msg):
    self.writebuffer.append(msg)

  def getAdmins(self):
    return self.admins

  def addAdmin(self, admin):
    self.admins.add(admin)

class XBMCBotAddon(xbmcaddon.Addon):
  # make a new irc client on init but get something to connect it with the 'start()' method
  def __init__(self):
    xbmcaddon.Addon(__id__)
    self.running=True
    self.client=IRCClient(self.getSetting('nick'), self.getSetting('auth'), self.getSetting('name'))
    if self.getSetting('debug') == 'true': self.client.setDebug(True)
  
  # if not yet connected, try to connect to a server (while this thread is active)
  def start(self):
    if self.isAlive(): return True
    self.client.log("Starting a fresh XBMCBot IRC client")
    while not self.client.connect(self.getSetting('server'), int(self.getSetting('port')), self.getSetting('ssl')=='true', self.getSetting('ipv6')=='true') and self.running:
      self.client.log("Unable to connect, retrying...")
      xbmc.sleep(10*1000)
    for c in __import__('commands').__all__:
      self.client.registerCommand(c)
    self.client.start()
    return True

  # stop this bot, if a client is still running, shut it down nicely
  def stop(self):
    self.running=False
    if self.client.isAlive():
      self.client.gracefullShutdown()

  # pretend to be alive if not supposed to be connected, otherwise check the client for running thread and connectivity
  def isAlive(self):
    if not self.getSetting('connect')=='true': return True
    return self.client.getPulse() and self.client.isAlive()  

# XBMCBot Monitor object starts a new XBMCBot and checks if it stays connected
class XBMCBotMonitor(xbmc.Monitor):
  
  # create a new bot on init
  def __init__(self):
    self.running=True
    self.xbmcbotAddon=XBMCBotAddon()

  # stop the watch thread and if the bot is alive, stop it too
  def stop(self):
    self.running=False
    if self.xbmcbotAddon.isAlive(): self.xbmcbotAddon.stop()

  # stop the bot on changed settings so the watch thread will restart it
  def onSettingsChanged(self):
    self.xbmcbotAddon.stop()

  # stop this monitor all together
  def onAbortRequested(self):
    self.stop()

  # keep an eye on the bot and make a new one if the current bot breaks
  def watch(self):
    while self.running:
      if not self.xbmcbotAddon.isAlive():
        self.xbmcbotAddon=XBMCBotAddon()
        self.xbmcbotAddon.start()
      xbmc.sleep(2000)
  
# start a new monitor thread and set it to watch the bot
if (__name__ == "__main__"):
  sys.dont_write_bytecode=True
  monitor=XBMCBotMonitor()
  monitor.watch()
