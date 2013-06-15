import command, json, xbmc, re

_DEBUG_JSON=False

class Command(command.Command):
  def localInit(self):
    self.wd={u'file':u'sources://',u'type':u'unknown',u'filetype':u'directory',u'label':u'sources://'} #holds current directory we're in (working directory)
    self.wdStack=[] #holds all previous directories
    self.ls=[] #holds current directory listing
    self.lsStack=[] #hold all previous directory listings
    self.media="video" #media type to work with
    self.more=[] #buffer for sending lines to the client

  def fillhelp(self):
    self.desc=dict({'!help xbmcctrl':'this modules offers extended help for admins',
                     })
    self.help=dict({'ls':'returns a listing of the current directory you\'re browsing',
                      'rels':'returns a directory listing without using the cached version',
                      'say':'broadcasts a message to all admins and to the local xbmc instance',
                      'more':'display the rest of the text buffer, if any',
                      'cd':'changes into a directory (full match first, first partial match second)',
                      'play':'plays a file (exact, fuzzy or url. in that order)',
                      'pause':'pause/resume current playback',
                      'stop':'stop all current playback',
                      'time':'tells the current position in playback as well as total time',
                      'seek':'skip to an absolute number of seconds or relative when using \'+\' or \'-\'',
                      'up':'moves up one directory',
                      'pwd':'lists current working path',
                     })

  def parsecommand(self, src, cmd, arg):
    nck=src.split('!')[0]
    if src in self.client.getAdmins():
      if cmd == "ls" or cmd == "dir":
        self.pushls(src, arg)

      if cmd == "rels":
        self.ls=[]
        self.pushls(src, arg)

      if cmd == "say":
        self.localNotify("%s says: %s" % (nck,arg))
        self.remoteNotify("%s says: %s" % (nck,arg))

      if cmd == "more":
        self.pushmore(src)

      if cmd == "cd":
        self.more=[]
        if arg == "..":
          if self.up(): self.more.append("Changed directory to %s" % self.wd['label'])
          else: self.more.append("Failed to change directory, already in root")
        else:
          if not len(self.ls): self.getls()
          if self.changeDirectory(arg):
            pwd=self.wd['label']
            self.more.append("Changed directory to %s" % pwd)
          else: self.more.append("Failed to find directory matching %s" % arg)
        self.pushmore(src)

      if cmd == "play" and not arg=="":
        self.more=[]
        result=self.open(arg)
        if result:
          self.more.append("Playing %s" % result)
          self.localNotify("%s started playing %s" % (nck,result))
        else: self.more.append("Failed playing %s" % arg)
        self.pushmore(src)

      if cmd == "download":
        self.more=[]
        result=self.getDownload(arg)

      if cmd == "pause":
        self.more=[]
        if self.pause(arg):
          self.more.append("Pause/Resume all playback")
          self.localNotify("%s toggled Pause/Resume" % nck)
        else: self.more.append("Failed to Pause/Resume playback")
        self.pushmore(src)

      if cmd == "stop":
        self.more=[]
        type=self.stop(arg)
        if type:
          self.more.append("%s playback stopped" % type)
          self.localNotify("%s stopped %s playback" % (nck,type))
        else: self.more.append("Failed to stop playback")
        self.pushmore(src)

      if cmd == "time":
        self.more=[]
        a=self.time(arg)
        if a: self.more.append(a)
        else: self.more.append("Error retrieving time")
        self.pushmore(src)

      if cmd == "seek":
        self.more=[]
        if self.seek(arg): self.more.append("Skipped to %s seconds" % arg)
        else: self.more.append("Unable to skip to %s seconds" % arg)
        self.pushmore(src)

      if cmd == "up":
        self.more=[]
        if self.up(): self.more.append("Changed directory to %s" % self.wd['label'])
        else: self.more.append("Failed to change directory, already in root")
        self.pushmore(src)

      if cmd == "pwd":
        tpath=""; self.more=[]
        for i in xrange(len(self.wdStack)):
          tpath+=self.wdStack[i]['label']+"/"
          if i<1: tpath=tpath[:-1]
        self.more.append("Current path: %s" % tpath+self.wd['label'])
        self.pushmore(src)

      if cmd == "built-in":
        result=xbmc.executebuiltin(arg)
        if result:
          self.more=[]
          self.more.append(str(result))
          self.pushmore(src)
          return True
        return False

  def jsonrpc(self, method, params=None):
    result={}
    q={"jsonrpc":"2.0", "id":None, "method":method}
    if params: q["params"]=params
    if _DEBUG_JSON: self.client.log(json.dumps(q))
    try: result=xbmc.executeJSONRPC(json.dumps(q))
    except: pass
    if _DEBUG_JSON: self.client.log(result)
    return json.loads(result)

  def getSources(self, media):
    a=self.jsonrpc("Files.GetSources", {"media":str(media)})
    if 'result' in a and 'sources' in a['result']:
      return a['result']['sources']
    return {}

  def getDirectory(self, path):
    a=self.jsonrpc("Files.GetDirectory", {"directory":str(path)})
    if 'result' in a and 'files' in a['result']:
      return a['result']['files']
    return {}

  def getDownload(self, name):
    for i in self.ls:
      if 'label' in i and i['label'].lower().count(name.lower()):
        print self.jsonrpc("Files.Download", {'path':i['file']})
        return True
    return False
  
  def getls(self):
    if self.wd['label']=='sources://':
      a=self.getSources(self.media)
      for i in a:
        i[u'filetype']=u'directory'
        i[u'type']=u'unknown'
      self.ls=a
      return a
    else:
      a=self.getDirectory(self.wd['file'])
      self.ls=a
      return a

  def changeDirectory(self, name):
    if not len(self.ls): self.getls()
    result=None
    for i in (x for x in self.ls if not result):
      if 'label' in i and i['filetype'] == 'directory':
        if i['label'].count(name): result=self.getDirectory(i['file'])
    for i in (x for x in self.ls if not result):
      if 'label' in i and i['filetype'] == 'directory':
        if i['label'].lower().count(name.lower()): result=self.getDirectory(i['file'])
    if result:
      self.wdStack.append(self.wd)
      self.lsStack.append(self.ls)
      self.wd=i
      self.ls=result
    return result

  def open(self, name):
    # see if we can match a youtube url, if so open video id with plugin
    youtube_re=re.compile('(https?://)?(www\.)?youtube\..*?v=(?P<id>[\w-]+)\?*.*')
    if youtube_re.match(name): return self.openyoutube(youtube_re.match(name).groupdict()['id'])

    # try and find a matching filename
    for i in (x for x in self.ls if 'label' in x):
      # try to do an exact match first
      if i['label'].count(name):
        if self.openurl(i['file']): return i['label']
    for i in (x for x in self.ls if 'label' in x):
      # try and no a case insensitive match next
      if i['label'].lower().count(name.lower()):
        if self.openurl(i['file']): return i['label']
    # if all fails, try to open it as an URL and return the results
    return self.openurl(name)

  def openyoutube(self, id):
    xbmc.log("XBMCBot:: playing YouTube ID %s" % id)
    file="plugin://plugin.video.youtube/?action=play_video&videoid=%s" % id
    xbmc.executebuiltin("PlayMedia(%s)" % file)
    return "YouTube ID: %s" % id

  def openurl(self, url):
    a=self.jsonrpc("Player.Open",{'item':{'file':url}})
    if not 'error' in a: return url
    return False

  def getCurrentPlayer(self, type):
    player=False
    stack=self.jsonrpc("Player.GetActivePlayers")
    if 'result' in stack and len(stack['result']):
      for item in stack['result']:
        # return first item from stack if no preference
        if type == 'all': return item
        # or return the first matching item of preference type
        if 'type' in item and item['type']==type: return item
    return player

  def getCurrentPlayerID(self, type):
    player=self.getCurrentPlayer(type)
    if player and 'playerid' in player: return player['playerid']
    return False

  def stop(self, type):
    if not type: return self.stopAll()
    playerid=self.getCurrentPlayerID(type)
    if playerid is not False:
      result=self.jsonrpc("Player.Stop", {'playerid':playerid})
      if 'error' in result: return False
      return type
    return False

  def stopAll(self):
    stopped=False
    while self.stop('all'): stopped='all'
    return stopped

  def pause(self, type):
    if not type: type='all'
    playerid=self.getCurrentPlayerID(type)
    if playerid is not False:
      type=self.getProperties(playerid)['type']
      result=self.jsonrpc("Player.PlayPause", {'playerid':playerid})
      if 'error' in result: return False
      return type
    return False

  def seek(self, secs):
    # return error if input is not absolute or relative value
    secs=str(secs)
    if not secs.lstrip('-+').isdigit(): return False

    playerid=self.getCurrentPlayerID('video')
    if playerid is False: playerid=self.getCurrentPlayerID('audio')
    if playerid is False: return False

    # get the current time, no need in seeking if nothing is playing
    currentTime=self.getCurrentTime(playerid)
    if not currentTime: return False

    # if number of seconds is absolute (i.e. not relative +/-) set the offset to 0
    if secs.isdigit(): currentTime=0
    # and in case of a relative value, calculate the target time including the offset
    targetTime=self.jsonTime(int(secs), currentTime)

    result=self.jsonrpc("Player.Seek",{'playerid':playerid,'value':targetTime})
    if 'error' in result: return False
    return True

  def jsonTime(self, secs, offset=0): #input in seconds, offset by seconds. returns json time string
    offset=abs(offset)
    if secs+offset<0: secs=0
    secs+=offset
    hours=secs/3600
    minutes=(secs/60)%60
    seconds=secs%60
    return {'hours':hours,'minutes':minutes,'seconds':seconds,'milliseconds':0}

  def time(self, type):
    if not type: type='all'
    playerid=self.getCurrentPlayerID(type)
    if playerid is not False:

      curint=self.getCurrentTime(playerid)
      perint=self.getPercentage(playerid)
      totint=self.getTotalTime(playerid)

      if not curint or not perint or not totint: return False
      perstr="%g%%" % perint
      curstr="%dh%dm%ds" % (curint/3600,(curint/60)%60,curint%60)
      totstr="%dh%dm%ds" % (totint/3600,(totint/60)%60,totint%60)
      return "%s/%s (%s)" % (curstr,totstr,perstr)
    return False

  def up(self):
    if not len(self.wdStack): return False
    else:
      self.wd=self.wdStack.pop()
      self.ls=self.lsStack.pop()
      return True

  def getProperties(self, playerid):
    a=self.jsonrpc("Player.GetProperties",{'playerid':playerid,'properties':['canrepeat','canmove','canshuffle','speed','percentage','playlistid','audiostreams','position','repeat','currentsubtitle','canrotate','canzoom','canchangespeed','type','partymode','subtitles','canseek','time','totaltime','shuffled','currentaudiostream','live','subtitleenabled']})
    if 'error' in a: return False
    else: return a['result']

  def getCurrentTime(self, playerid): #input player id as integer. returns current time in seconds
    player=self.getProperties(playerid)
    if not player or 'time' not in player: return False
    curstr=player['time']
    curint=(curstr['hours']*3600)+(curstr['minutes']*60)+curstr['seconds']
    return curint
  
  def getPercentage(self, playerid):
    player=self.getProperties(playerid)
    if not player or 'percentage' not in player: return False
    perstr=player['percentage']
    perint=int(perstr*10)/10.0
    return perint

  def getTotalTime(self, playerid): #input player id in integer. returns total running time in seconds
    player=self.getProperties(playerid)
    if not player or 'totaltime' not in player: return False
    totstr=player['totaltime']
    totint=(totstr['hours']*3600)+(totstr['minutes']*60)+totstr['seconds']
    return totint

  def pushls(self, src, arg):
    if not len(self.ls): self.getls() #refresh current directory listing if empty
    self.more=[] #clear more
    for i in self.ls: #check every entry in the dirlist
      if 'label' in i and i['label'].lower().count(arg.lower()): #if the name matches the search display it, if search is empty it always matches
        if 'filetype' in i and i['filetype'] == 'directory': self.more.append("D %s" % i['label']) #if it was a directory append "D"
        else: self.more.append("F %s" % i['label']) #otherwise it's a file and append "F"
    self.pushmore(src) #get started on printing the first part of the buffer

  def pushmore(self, src):
    for i in xrange(10):
      if len(self.more):
        self.client.sendPrivateReply(src, self.more.pop(0), True)
    if len(self.more):
      self.client.sendPrivateReply(src, "type 'more' for more", True)

  def remoteNotify(self, message):
    self.client.sendAllReply(message)

  def localNotify(self, message, displaytime=10000):
    params={"title":"XBMCBot", "message":message, "displaytime":displaytime}
    self.jsonrpc('GUI.ShowNotification', params)