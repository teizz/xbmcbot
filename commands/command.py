class Command():
  def __init__(self, name, client):
    self.name=name
    self.client=client
    self.desc=dict({})
    self.help=dict({})
    self.localInit()
    self.fillhelp()
  
  def getName(self):
    return self.name

  def description(self):
    return self.desc

  def extendedhelp(self):
    return self.help

  def parseline(self, match):
    if not len(match): return False
    if not 'src' in match or not 'message' in match: return False
    src=match['src']
    msg=match['message'].split(None,1)
    cmd="".join(msg[:1])
    arg="".join(msg[1:])
    return self.parsecommand(src,cmd,arg)
   
  def localInit(self):
    # do any init here for stuff you need, command will try to init this after main init
    pass
 
  def fillhelp(self):
    # this gets called by init to populate description and help
    raise NotImplementedError
  
  def parsecommand(self, src, cmd, arg):
    # this is where the magic should happen
    raise NotImplementedError