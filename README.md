# Pybot2 IRC Bot
Simple, hand-rolled, async IRC bot. Run with `./pybot <config file>`.
An example config file is provided under example-config.json.

## Modules
**anime**: Danbooru search by scraping the page html.  
**channel**: Channel join/part management functions.  
**help**: Commands to display help for other commands.  
**join_ad**: Auto-send a message to anyone who joins the channel.  
**module**: Manage (remove, load, reload) modules.  
**nick**: Change the bot's nick.  
**qchoice**: Choose between options with the https://qrng.anu.edu.au/ quantum random number service.  
**rpg**: Small prototype text RPG.  
**rss**: Forward RSS feeds straight into an IRC channel.  
**say**: Send messages as the bot!  
**talkbot**: Send a message to the bot, store it, get a random stored message back.  
**word_trigger**: Add triggers to respond to IRC messages. Useful for rewriting links.