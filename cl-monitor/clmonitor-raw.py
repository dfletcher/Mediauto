#/usr/bin/env python


import dbus
import time
import atexit
import gobject
from dbus import glib

gobject.threads_init()
glib.init_threads()
bus = dbus.SystemBus()

def sigwatch(*args, **kwargs):
  print 'signal: ' + str(kwargs) + '; ' + str(args)
  print

if __name__ == '__main__':
  bus.add_signal_receiver(
    sigwatch,
    None,
    None,
    None,
    None,
    sender_keyword = 'sender',
    destination_keyword = 'destination',
    interface_keyword = 'interface',
    member_keyword = 'member',
    path_keyword = 'path',
    message_keyword = 'message'
  )
  gobject.MainLoop().run()

