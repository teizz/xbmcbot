import command, json, xbmc, re

_DEBUG_JSON=True

class FileIndex():
  def __init__(self, media='video'):
    self.media=media
    self.pwd=['sources://']
    self.tree=dict({self.getPwd():self.getSources(self.media)})

  def jsonrpc(self, method, params=None):
    result={}
    q={"jsonrpc":"2.0", "id":None, "method":method}
    if params: q["params"]=params
    if _DEBUG_JSON: print(json.dumps(q))
    try: result=xbmc.executeJSONRPC(json.dumps(q))
    except: pass
    if _DEBUG_JSON: print(result)
    return json.loads(result)

  def getSources(self, media):
    a=self.jsonrpc("Files.GetSources", {"media":str(media)})
    if 'result' in a and 'sources' in a['result']:
      return [dict(x.items()+[('filetype','directory')]) for x in a['result']['sources']]
    return []

  def getDirectory(self, path):
    a=self.jsonrpc("Files.GetDirectory", {"directory":str(path)})
    if 'result' in a and 'files' in a['result']:
      return a['result']['files']
    return []

  def getFileList(self, match):
    result=[]
    for i in self.tree[self.getPwd()]: #check every entry in the dirlist
      if 'label' in i and i['label'].lower().count(match.lower()): #if the name matches the search display it, empty match variables always match
        if 'filetype' in i and i['filetype'] == 'directory': result.append("D %s" % i['label']) #if it was a directory append "D"
        else: result.append("F %s" % i['label']) #otherwise it's a file and append "F"
    return result

  def forceUpdate(self):
    if len(self.pwd)<=1:
      self.tree[self.getPwd()]=self.getSources(self.media)
      return True
    else: return changeDirectory(self.pwd.pop())

  # current working path just a nice representation of the dir stack
  def getPwd(self):
    return str().join([self.pwd[0]]+[i+"/" for i in self.pwd if not i == 'sources://'])
 
  # current dir is always the last item on the dir stack
  def getCurrentDir(self):
    return self.pwd[-1]

  def changeDirectory(self, name):
    result=None
    # go through all items as long as no result is found, the item has a label and is a directory
    for item in (x for x in self.tree[self.getPwd()] if not result and 'label' in x and x['filetype']=='directory'):
      # if the item partially matches the name being changed to
      if item['label'].count(name):
        # check if the index has been chached
        testpath=self.getPwd()+item['label']+"/"
        if testpath in self.tree: result=self.tree[testpath]
        # if not get a new index for this directory
        else: result=self.getDirectory(item['file'])
          
    for item in (x for x in self.tree[self.getPwd()] if not result and 'label' in x and x['filetype']=='directory'):
      # if the item partially matches the name being changed to (this time case-insensitive)
      if item['label'].lower().count(name.lower()):
        # check if the index has been chached
        testpath=self.getPwd()+item['label']+"/"
        if testpath in self.tree: result=self.tree[testpath]
        # if not get a new index for this directory
        else: result=self.getDirectory(item['file'])

    # if a result was found, update the dir stack and maybe update the index
    if result:
      self.pwd.append(item['label'])
      if not testpath in self.tree:
        self.tree[self.getPwd()]=result
    return result is not None

  def up(self):
    # if already at top level, don't try to go any higher
    if len(self.pwd) <= 1: return False
    # otherwise chop the last directory from the path, the index can be kept for later use
    else: self.pwd.pop()
    return True

class Command(command.Command):
  def localInit(self):
    self.masters=dict()

  def fillhelp(self):
    self.desc=dict({'!help xbmcctrl':'this modules offers extended help for admins',
                     })
    self.help=dict({'ls':'returns a listing of the current directory you\'re browsing',
                    'dir':'same as ls',
                    'rels':'returns a directory listing without using the cached version',
                    'cd':'changes into a directory (full match first, first partial match second)',
                    'up':'moves up one directory',
                    'pwd':'lists current working path',
                    'play':'plays a file (exact, fuzzy or url. in that order)',
                    'pause':'pause/resume current playback',
                    'stop':'stop all current playback',
                    'time':'tells the current position in playback as well as total time',
                    'seek':'skip to an absolute number of seconds or relative when using \'+\' or \'-\'',
                    'volume':'sets volume to something between 0 (mute) and 100',
                    'mute':'sets volumet to 0',
                    'zoom':'toggles between aspect ratios',
                    'info':'displays info on current playing item on screen',
                    'fullscreen':'hides or displays the fullscreen menu',
                    'say':'broadcasts a message to all admins and to the local xbmc instance',
                    'more':'display the rest of the text buffer, if any',
                     })

  def parsecommand(self, src, cmd, arg):
    nck=src.split('!')[0]
    if src in self.client.getAdmins():
      
      if not src in self.masters:
        self.masters[src]=dict({'index':FileIndex(),'buffer':[]})
      
      if cmd == "ls" or cmd == "dir":
        self.masters[src]['buffer']=self.masters[src]['index'].getFileList(arg)
        self.pushmore(src)

      if cmd == "rels":
        if self.masters[src]['index'].forceUpdate():
          self.masters[src]['buffer']=self.masters[src]['index'].getFileList(arg)
        else: self.masters[src]['buffer']=['Failed to get a file listing']
        self.pushmore(src)

      if cmd == "cd":
        if arg == "..": success = self.masters[src]['index'].up()
        else: success = self.masters[src]['index'].changeDirectory(arg)
        if success: self.masters[src]['buffer']=["Changed directory to %s" % self.masters[src]['index'].getCurrentDir()]
        else: self.masters[src]['buffer']=["Failed to change directory"]
        self.pushmore(src)

      if cmd == "up" or cmd == "cd..":
        if self.up(): self.masters[src]['buffer']=["Changed directory to %s" % self.masters[src]['index'].getCurrentDir()]
        else: self.masters[src]['buffer']=["Failed to change directory"]
        self.pushmore(src)

      if cmd == "pwd":
        self.masters[src]['buffer']=["Current path: %s" % self.masters[src]['index'].getPwd()]
        self.pushmore(src)

      if cmd == "play":
        if len(arg)<=0:
          if self.pause(arg):
            self.masters[src]['buffer']=["Pause/Resume all playback"]
            self.localNotify("%s toggled Pause/Resume" % nck)
          else: self.masters[src]['buffer']=["Failed to Pause/Resume playback"]
        else:
          result=self.open(arg)
          if result:
            self.masters[src]['buffer']=["Playing %s" % result]
            self.localNotify("%s started playing %s" % (nck,result))
          else: self.masters[src]['buffer']=["Failed playing %s" % arg]
        self.pushmore(src)

      if cmd == "pause":
        if self.pause(arg):
          self.masters[src]['buffer']=["Pause/Resume all playback"]
          self.localNotify("%s toggled Pause/Resume" % nck)
        else: self.masters[src]['buffer']=["Failed to Pause/Resume playback"]
        self.pushmore(src)

      if cmd == "stop":
        type=self.stop(arg)
        if type:
          self.masters[src]['buffer']=["%s playback stopped" % type]
          self.localNotify("%s stopped %s playback" % (nck,type))
        else: self.masters[src]['buffer']=["Failed to stop playback"]
        self.pushmore(src)

      if cmd == "time":
        a=self.time(arg)
        if a: self.masters[src]['buffer']=[a]
        else: self.masters[src]['buffer']=["Error retrieving time"]
        self.pushmore(src)

      if cmd == "seek":
        if len(arg)>0 and self.seek(arg): self.masters[src]['buffer']=["Skipped to %s seconds" % arg]
        else: self.masters[src]['buffer']=["Unable to skip to %s seconds" % arg]
        self.pushmore(src)

      if cmd == "volume":
        if len(arg)>0 and self.volume(arg): self.masters[src]['buffer']=["Set volume to %s" % arg]
        else: self.masters[src]['buffer']=["Unable to set volume to %s" % arg]
        self.pushmore(src)

      if cmd == "mute":
        if self.volume("0"): self.masters[src]['buffer']=["Toggled mute/unmute"]
        else: self.masters[src]['buffer']=["Failed to toggle mute/unmute"]

      if cmd == "say":
        self.localNotify("%s says: %s" % (nck,arg))
        self.remoteNotify("%s says: %s" % (nck,arg))

      if cmd == "more":
        self.pushmore(src)

      if cmd == "zoom":
        if self.executeAction("aspectratio"): self.masters[src]['buffer']=["Toggled aspect ratio"]
        else: self.masters[src]['buffer']=["Failed to toggle aspect ratio"]

      if cmd == "info":
        if self.executeAction("info"): self.masters[src]['buffer']=["Toggled info"]
        else: self.masters[src]['buffer']=["Failed to toggle info"]

      if cmd == "fullscreen":
        if self.executeAction("fullscreen"): self.masters[src]['buffer']=["Toggled fullscreen display"]
        else: self.masters[src]['buffer']=["Failed to fullscreen display"]

      # Dangerous unchecked functions which should only be available when debuggin is turned on

      if cmd == "built-in" and client.debug:
        result=xbmc.executebuiltin(arg)
        if result:
          self.masters[src]['buffer']=[str(result)]
          self.pushmore(src)
      
      if cmd == "json-rpc" and client.debug:
        method=str().join(arg.split(None,1)[:1])
        params=str().join(arg.split(None,1)[1:])
        if len(params)>0: result=self.jsonrpc(method, json.loads(params))
        else: result=self.jsonrpc(method)
        if result:
          self.masters[src]['buffer']=[str(result)]
          self.pushmore(src)

  def jsonrpc(self, method, params=None):
    result={}
    q={"jsonrpc":"2.0", "id":None, "method":method}
    if params: q["params"]=params
    if _DEBUG_JSON: self.client.log(json.dumps(q))
    try: result=xbmc.executeJSONRPC(json.dumps(q))
    except: pass
    if _DEBUG_JSON: self.client.log(result)
    return json.loads(result)

  def executeAction(self, action):
    if 'error' in self.jsonrpc("Input.ExecuteAction", {"action":action}): return False
    return True
  
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

  def volume(self, vol):
    # return error if input is not absolute or relative value
    try: vol=int(vol)
    except: return False
    if vol<=0: return self.mute()
    elif not self.mute(False): return False
    else: return 'error' not in self.jsonrpc("Application.SetVolume",{'volume':int(vol)})
  
  def mute(self, toggle=True):
    if 'error' in self.jsonrpc("Application.SetMute",{'mute':False}): return False
    elif toggle: return 'error' not in self.jsonrpc("Application.SetMute",{'mute':True})
    return True

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

  def pushmore(self, src):
    for i in xrange(10):
      if len(self.masters[src]['buffer']):
        self.client.sendPrivateReply(src, self.masters[src]['buffer'].pop(0), True)
    if len(self.masters[src]['buffer']):
      self.client.sendPrivateReply(src, "type 'more' for more", True)

  def remoteNotify(self, message):
    self.client.sendAllReply(message)

  def localNotify(self, message, displaytime=10000):
    params={"title":"XBMCBot", "message":message, "displaytime":displaytime}
    self.jsonrpc('GUI.ShowNotification', params)