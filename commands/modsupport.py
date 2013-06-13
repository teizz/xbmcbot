import command
class Command(command.Command):
  
  def fillhelp(self):
    self.desc=dict({"!list":"print all loaded command modules",
                      "!load <name>":"load a new command module",
                      "!unload <name>":"unload an existing command module",
                      "!reload <name>":"reload an existing command module"})
  
  def parsecommand(self, src, cmd, arg):
    #shutting down actions are admin actions
    if src in self.client.getAdmins():
      if cmd == "!list":
        for i in self.client.getCommands():
          self.client.sendPrivateReply(src,i.getName(),True)
      if cmd == "!load":
        self.client.registerCommand(arg)
      if cmd == "!unload":
        self.client.unregisterCommand(arg)
      if cmd == "!reload":
        self.client.unregisterCommand(arg)
        self.client.registerCommand(arg)