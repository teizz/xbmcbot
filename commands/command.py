# This is the generic 'command' interface. The IRC client initiates it with the name of the module and supplies
# a callback hook to allow the command object ot interface with the client.
class Command():
  def __init__(self, name, client):
    self.name=name
    self.client=client
    self.desc=dict({})
    self.help=dict({})
    self.localInit()
    self.fillhelp()
  
  # Returns the name of this command module
  def getName(self):
    return self.name

  # Gives a description of commands handled by this module
  def description(self):
    return self.desc

  # Gives extended help on this module. For when there are to many
  # commands or commands very specific to this module
  def extendedhelp(self):
    return self.help

  # Called by the client to handle a line. It in turn calls the parsecommand method
  # which needs to be written by the author implementing this interface
  def parseline(self, match):
    if not len(match): return False
    if not 'src' in match or not 'message' in match: return False
    src=match['src']
    msg=match['message'].split(None,1)
    cmd="".join(msg[:1])
    arg="".join(msg[1:])
    return self.parsecommand(src,cmd,arg)

  # Any local init that needs to be done can be put here. It will be called by the command __init__()
  def localInit(self):
    # do any init here for stuff you need, command will try to init this after main init
    pass
 
  # Called by __init__ to populate help and extended help.
  # Example: self.desc={'command':'executes command and does stuff',
  #                     'othercomm <number>':'does a <number> of things',
  #                    }
  def fillhelp(self):
    # this gets called by init to populate description and help
    raise NotImplementedError

  # Called with arguments src (sender in full nick!~user@hostname.fqdn.ext),
  #                       cmd (first word of the line), and
  #                       arg (any other words after the first)
  def parsecommand(self, src, cmd, arg):
    # this is where the magic should happen
    raise NotImplementedError