import command, time
class Command(command.Command):
  def localInit(self):
    self.time=time.time()  

  def fillhelp(self):
    self.desc=dict({".uptime":"Reports how long the bot has been running.",
                     })

  def parsecommand(self, src, cmd, arg):
    if cmd == ".uptime":
      uptime=int(time.time()-self.time)
      minutes=str((uptime/60)%60).zfill(2)
      hours=str((uptime/3600)%24).zfill(2)
      days=str(uptime/86400)
      current=time.strftime("%H:%M:%S")
      uptimestr=("%s up %s days, %s:%s" % (current,days,hours,minutes))
      self.client.sendPrivateReply(src,uptimestr)
