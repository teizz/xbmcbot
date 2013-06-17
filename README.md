XBMCBot
=======

Summary:
--------
XBMCBot is an IRC bot which allows you to get a listing of videos and have (at this time) limited control over playback. Send it a message with '.help' for commands.

Functions:
---------
* !list         print all loaded command modules
* !reload name  reload an existing command module
* !load name    load a new command module
* !unload name  unload an existing command module
* !raw cmd      Sends a raw IRC command to the server
* !shutdown     Requests a graceful disconnect from the server
* !die          Disconnects from the server without saying goodbye
* !eventlog [#] Send last # of lines in eventlog (default:10)
* !help module  Get extended help on a certain module
* .help         Lists available commands
* .auth code    Authenticates to enable admin commands
* .echo msg     Returns the string you send via private message
* .version      returns the version of xbmcbot
* .uptime       Reports how long the bot has been running.
* ls            returns a listing of the current directory you're browsing
* dir           same as 'ls'
* rels          returns a directory listing without using the cached version
* cd            changes into a directory (full match first, first partial match second)
* up            moves up one directory
* play          plays a file (exact, fuzzy or url. in that order)
* pause         pause/resume current playback
* stop          stop all current playback
* pwd           lists current working path
* say           broadcasts a message to all admins and to the local xbmc instance
* time          tells the current position in playback as well as total time
* seek          skip to an absolute number of seconds or relative when using '+' or '-'
* more          display the rest of the text buffer, if any
