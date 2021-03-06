import sys
import threading
from pathlib import Path

from twisted.internet import defer, endpoints, protocol, reactor, task
from twisted.python import log
from twisted.words.protocols import irc

from config import *
from Markov import *

class BotProtocol(irc.IRCClient):
    nickname = NICKNAME
    password = PASSWORD

    def __init__(self):
        self.deferred = defer.Deferred()

        # Markov init
        self.markov = Markov()
        first = True
        for filename in sys.argv:
            if Path(filename).is_file() and not first:
                self.markov.ScanFile(filename)
            first = False

    def connectionLost(self, reason):
        self.deferred.errback(reason)

    def signedOn(self):
        # This is called once the server has acknowledged that we sent
        # both NICK and USER.
        for channel in self.factory.channels:
            self.join(channel)

    # Obviously, called when a PRIVMSG is received.
    def privmsg(self, user, channel, message):
        nick, _, host = user.partition('!')
        message = message.strip()
        #self.markov.AddMessage(user, message)
        if not message.startswith('!'):  # not a trigger command
            self.markov.AddMessage(nick, message) # Add message to database
            return
        command, sep, rest = message.lstrip('!').partition(' ')
        # Get the function corresponding to the command given.
        func = getattr(self, 'command_' + command, None)
        # Or, if there was no function, ignore the message.
        if func is None:
            return
        # maybeDeferred will always return a Deferred. It calls func(rest), and
        # if that returned a Deferred, return that. Otherwise, return the
        # return value of the function wrapped in
        # twisted.internet.defer.succeed. If an exception was raised, wrap the
        # traceback in twisted.internet.defer.fail and return that.
        d = defer.maybeDeferred(func, rest)
        # Add callbacks to deal with whatever the command results are.
        # If the command gives error, the _show_error callback will turn the
        # error into a terse message first:
        d.addErrback(self._showError)
        # Whatever is returned is sent back as a reply:
        if channel == self.nickname:
            # When channel == self.nickname, the message was sent to the bot
            # directly and not to a channel. So we will answer directly too:
            d.addCallback(self._sendMessage, nick)
        else:
            # Otherwise, send the answer to the channel, and use the nick
            # as addressing in the message itself:
            d.addCallback(self._sendMessage, channel, nick)

    def _sendMessage(self, msg, target, nick=None):
        if nick:
            msg = '%s, %s' % (nick, msg)
        self.msg(target, msg)

    def _showError(self, failure):
        return failure.getErrorMessage()

    def command_stats(self, rest):
        self._sendMessage(self.markov.GetStats(rest), '#' + CHANNEL)

    #def command_ping(self, rest):
    #    return 'Pong.'

    def command_markov(self, rest):
        self._sendMessage(self.markov.CreateMessage(), '#' + CHANNEL)

    #def command_saylater(self, rest):
    #    when, sep, msg = rest.partition(' ')
    #    when = int(when)
    #    d = defer.Deferred()
        # A small example of how to defer the reply from a command. callLater
        # will callback the Deferred with the reply after so many seconds.
    #    reactor.callLater(when, d.callback, msg)
        # Returning the Deferred here means that it'll be returned from
        # maybeDeferred in privmsg.
    #    return d

class IRCFactory(protocol.ReconnectingClientFactory):
    protocol = BotProtocol
    channels = ['#' + CHANNEL]

def main(reactor, description):
    endpoint = endpoints.clientFromString(reactor, description)
    factory = IRCFactory()
    d = endpoint.connect(factory)
    d.addCallback(lambda protocol: protocol.deferred)
    return d


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    task.react(main, ['tcp:' + SERVER])
