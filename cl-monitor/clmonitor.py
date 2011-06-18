#/usr/bin/env python

import sys
import dbus
import time
import atexit
import gobject
import curses
import dbus.service
from dbus import glib

gobject.threads_init()
glib.init_threads()
bus = dbus.SystemBus()
activeprocs = {}
stdscr = None

n = 1
def draw():
  global activeprocs, n
  stdscr.clear()
  i = 1
  n += 1
  for upi in activeprocs.keys():
    complete = activeprocs[upi]
    n = int(complete * 50)
    i2 = i+1
    a = upi.split('/')
    action = a[-1]
    label = a[-2]
    stdscr.addstr(i, 5, action + ': ' + label)
    stdscr.addstr(i2, 5, '[')
    stdscr.addstr(i2, 6, '=' * n)
    if n != 0: stdscr.addstr(i2, n+6, '>')
    stdscr.addstr(i2, 56, ']')
    stdscr.addstr(i2, 58, '%.2f%%' % (complete * 100))
    i += 2
  stdscr.refresh()

def process_queued(type, upi):
  global activeprocs
  activeprocs[upi] = 0.0
  draw()

def process_started(type, upi):
  global activeprocs
  activeprocs[upi] = 0.0
  draw()

def process_ended(type, upi):
  global activeprocs
  if upi in activeprocs: del activeprocs[upi]
  draw()

def process_progress(type, upi, complete):
  global activeprocs
  activeprocs[upi] = complete
  draw()

def mainloop():
  c = stdscr.getch()
  if c: sys.exit(0)
  return True

def cleanup():
  curses.nocbreak()
  stdscr.keypad(0)
  curses.echo()
  curses.endwin()

if __name__ == '__main__':
  stdscr = curses.initscr()
  curses.noecho()
  curses.cbreak()
  stdscr.keypad(1)
  atexit.register(cleanup)
  bus.add_signal_receiver(
    process_queued,
    'ProcessQueued',
    'org.mediauto.Mediauto.Manager',
    'org.mediauto.Mediauto',
    '/org/mediauto/Mediauto/Manager'
  )
  bus.add_signal_receiver(
    process_started,
    'ProcessStarted',
    'org.mediauto.Mediauto.Manager',
    'org.mediauto.Mediauto',
    '/org/mediauto/Mediauto/Manager'
  )
  bus.add_signal_receiver(
    process_progress,
    'PercentComplete',
    'org.mediauto.Mediauto.Manager',
    'org.mediauto.Mediauto',
    '/org/mediauto/Mediauto/Manager'
  )
  bus.add_signal_receiver(
    process_ended,
    'ProcessEnded',
    'org.mediauto.Mediauto.Manager',
    'org.mediauto.Mediauto',
    '/org/mediauto/Mediauto/Manager'
  )
  draw()
  #gobject.timeout_add(1000, mainloop)
  gobject.MainLoop().run()

