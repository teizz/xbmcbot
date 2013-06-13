import command
class Command(command.Command):
  
  def fillhelp(self):
    self.desc=dict({".echo <msg>":"Returns the string you send via private message",
                      ".auth <code>":"Authenticates to enable admin commands",
                      ".help":"Lists available commands",
               })
    
  def parsecommand(self, src, cmd, arg):
    #shutting down actions are admin actions
    if cmd == ".echo":
      self.client.sendPrivateReply(src,arg)
    if cmd == ".auth":
      if self.client.doAuth(arg):
        self.client.addAdmin(src)
        self.client.sendPrivateReply(src,"Oh %s! I love you so very very much now!" % src.split("!")[0],True)
    if cmd == ".help":
      for c in self.client.getCommands():
        for key, value in c.description().items():
          if not key.startswith('!') or src in self.client.getAdmins():
            self.client.sendPrivateReply(src, "%s%s" % (key.ljust(16),value), True)
