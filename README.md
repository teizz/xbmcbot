# XBMCBot

## Summary:
XBMCBot is an IRC bot which allows you to get a listing of videos and have (at this time) limited control over playback. Send it a message with '.help' for commands.

## Commands:
* **bold text** are manditory parameters
* *italic text* are optional parameters

### Public
| Command	| Arguments	| Description					|
|:--------------|:--------------|:----------------------------------------------|
| .help		|		| Lists available commands			
| .auth		| **code**	| Authenticates to enable admin commands	
| .echo		| **text**	| Returns the text you send via private message	
| .version	|		| returns the version of xbmcbot		
| .uptime	|		| Reports how long the bot has been running.	

### Admin
| Command	| Arguments	| Description					|
|:--------------|:--------------|:----------------------------------------------|
| !list		|		| Print all loaded command modules
| !reload	| **module**	| Reload an existing command module
| !load		| **module**	| Load a new command module
| !unload	| **module**	| Unload an existing command module
| !raw		| **command**	| Sends a raw IRC command to the server
| !shutdown	|		| Requests a graceful disconnect from the server
| !die		|		| Disconnects from the server without saying goodbye
| !eventlog	| *# lines*	| Send last # of lines in eventlog (default:10)
| !help		| **module**	| Get extended help on a certain module

### XBMC Control Module:
| Command	| Arguments	| Description					|
|:--------------|:--------------|:----------------------------------------------|
| ls		| **search**	| returns a listing of the current directory you're browsing
| dir		| 		| same as 'ls'
| rels		| **search**	| returns a directory listing without using the cached version
| cd		| **directory**	| changes into a directory (full match first, first partial match second, and goes home when no comment is given)
| up		| 		| moves up one directory
| play		| **item**	| plays a file (exact, fuzzy or url. in that order). Resumes if no argument is given
| pause		| 		| pause/resume current playback
| stop		| 		| stop all current playback
| pwd		| 		| lists current working path
| say		| **message**	| broadcasts a message to all admins and to the local xbmc instance
| time		| 		| tells the current position in playback as well as total time
| seek		| *+/-* **time**| skip to an absolute number of seconds or relative when using '+' or '-'
| more		| 		| display the rest of the text buffer, if any
| volume	| **percent**	| sets volume to something between 0 (mute) and 100
| mute		| 		| sets volume to 0
| zoom		| *# times*	| toggles between aspect ratios
| info		| 		| displays info on current playing item on screen
| fullscreen	| 		| hides or displays the fullscreen menu