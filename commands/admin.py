import command
class Command(command.Command):

  def fillhelp(self):
    self.desc=dict({"!shutdown":"Requests a graceful disconnect from the server",
                      "!die":"Disconnects from the server without saying goodbye",
                      "!raw <cmd>":"Sends a raw IRC command to the server",
                      "!help <module>":"Get extended help on a certain module",
               })
  
  def parsecommand(self, src, cmd, arg):
    #shutting down actions are admin actions
    if src in self.client.getAdmins():
      if cmd == "!shutdown": #request connection close
        self.client.sendPrivateReply(src,"Asking the server to close my connection. Bye bye my love.",True)
        self.client.sendQuit()
      if cmd == "!die": #force connection close
        self.client.sendPrivateReply(src,"Why?! Why did you kill me? It hurts so bad.",True)
        self.client.disconnect()
      if cmd == "!raw":
        self.client.sendRaw(arg)
      if cmd == "!help":
        for c in self.client.getCommands():
          if c.getName() == arg:
            for key, value in c.extendedhelp().items():
              self.client.sendPrivateReply(src, "%s%s" % (key.ljust(16),value), True)
      if cmd == "!eventlog":
        if arg.isdigit(): arg=int(arg)
        else: arg=10
        if len(self.client.eventlog)<arg: arg=len(self.client.eventlog)
        for i in xrange(arg,0,-1):
          self.client.sendPrivateReply(src,self.client.eventlog[-i], True)
        self.client.log("sent %d loglines which are omitted from eventlog" % arg)

