PyrkovBot
=====
This is a fun little IRC bot that uses markov chains to create messages based on chat history. The name comes from a mix of Python and Markov.

Commands
---
* !markov - The bot creates and posts a message to chat
* !stats nickname - Print the top 10 most commonly used words by that user

Other features
---
* run "ExportWordList.py outputfilename.txt" to get a text file with all the words in the database and how many times they have showed up. The idea is to use this for creating word clouds (https://worditout.com/word-cloud/create).

Dependencies
---
* Twisted 17.1.0
* tqdm 4.11.2
* sqlite3
