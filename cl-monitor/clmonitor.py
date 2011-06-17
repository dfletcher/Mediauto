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
processes = {}
stdscr = None

n = 1
def draw():
  global processes, n
  stdscr.clear()
  i = 0
  #stdscr.addstr(str(processes))
  stdscr.addstr('n: %d' % n)
  n += 1
  for upi in processes.keys():
    complete = processes[upi]
    n = int(complete * 20)
    stdscr.addstr(i, 2, upi[-15:])
    stdscr.addstr(i, 17, '[')
    stdscr.addstr(i, 18, '=' * n)
    stdscr.addstr(i, n+1, '>')
    stdscr.addstr(i, 37, ']')
    i += 2
  stdscr.refresh()

def process_started(type, upi):
  global processes
  processes[upi] = 0.0

def process_ended(type, upi):
  global processes
  del processes[upi]

def process_progress(type, upi, complete):
  global processes
  processes[upi] = complete

def sigwatch(*args):
  #print 'signal: ' + str(args)
  pass

def mainloop():
  c = stdscr.getch()
  if c: sys.exit(0)
  draw()
  return True

def cleanup():
  curses.nocbreak()
  stdscr.keypad(0)
  curses.echo()
  curses.endwin()
  global processes
  print str(processes)

if __name__ == '__main__':
  stdscr = curses.initscr()
  curses.noecho()
  curses.cbreak()
  stdscr.keypad(1)
  atexit.register(cleanup)
  bus.add_signal_receiver(
    sigwatch,
    None,
    None,
    'org.mediauto.Mediauto',
    None
  )
  bus.add_signal_receiver(
    process_progress,
    'PercentComplete',
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
    process_ended,
    'ProcessEnded',
    'org.mediauto.Mediauto.Manager',
    'org.mediauto.Mediauto',
    '/org/mediauto/Mediauto/Manager'
  )
  draw()
  gobject.timeout_add(1000, mainloop)
  gobject.MainLoop().run()
  #while mainloop():
  #  time.sleep(1)
