#/usr/bin/env python

import dbus
import time
import gobject
import threading
import dbus.service
from dbus import glib
from dbus.service import BusName

import mediauto.module
import mediauto.config

# Variables
active = {}
gobject.threads_init()
glib.init_threads()
bus = dbus.SystemBus()
processor_queue = []
running_queue = []

# Constants
MAX_PROCESSES = int(mediauto.config.variable('processor.max'))

class MediautoManager(dbus.service.Object):
  def __init__(self, path):
    self.busname = dbus.service.BusName('org.mediauto.Mediauto', bus)
    dbus.service.Object.__init__(self, self.busname, path)
  @dbus.service.signal(dbus_interface='org.mediauto.Mediauto.Manager', signature='ss')
  def ProcessQueued(self, ptype, upi): pass
  @dbus.service.signal(dbus_interface='org.mediauto.Mediauto.Manager', signature='ss')
  def ProcessStarted(self, ptype, upi): pass
  @dbus.service.signal(dbus_interface='org.mediauto.Mediauto.Manager', signature='ss')
  def ProcessEnded(self, ptype, upi): pass
  @dbus.service.signal(dbus_interface='org.mediauto.Mediauto.Manager', signature='ssd')
  def PercentComplete(self, ptype, upi, complete): pass
manager = MediautoManager('/org/mediauto/Mediauto/Manager')

# TODO: real logs.
def log(msg):
  print msg

def queue_processes(udi, type, info):
  global active
  active[udi] = info
  processor = mediauto.module.processor_instance(type, info)
  if processor:
    processes = mediauto.config.insert_rule(type)
    for process in processes:
      processor.queue(process)
      p = processor.get(process)
      manager.ProcessQueued(p.type(), p.upi())
    processor_queue.append(processor)
    #log('insert rule: %s' % processes)

def hal_device_insert(udi):

  time.sleep(5) # Wait for drive to settle.

  device = bus.get_object('org.freedesktop.Hal', udi)
  iface = dbus.Interface(device, 'org.freedesktop.Hal.Device')

  # This is handy for iterating over device properties for debugging.
  #props = iface.GetAllProperties()
  #log('\n'.join(('%s: %s' % (k, props[k]) for k in props)) + '\n')

  # Currently do nothing if a blank CD or DVD is inserted.
  if iface.GetPropertyBoolean('volume.disc.is_blank'):
    log('Blank CD/DVD inserted, ignoring it.')
    return

  # Find a processor constructor function. for example "dvd_rom_processor".
  type = iface.GetPropertyString('volume.disc.type')

  # Gather media and device info.
  label = iface.GetPropertyInteger('volume.label')
  info = {
    'udi': udi,
    'upi': '/org/mediauto/Mediauto/Process/' + type + '/' + label,
    'type': type,
    'device': iface.GetPropertyInteger('block.device'),
    'label': label,
    'size': iface.GetPropertyInteger('volume.size')
  }
  queue_processes(udi, type, info)

def hal_device_remove(udi):
  if udi in active.keys(): del active[udi]

def udisks_device_changed(udi):
  proxy = bus.get_object('org.freedesktop.UDisks', udi)
  iface = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
  props = iface.GetAll('org.freedesktop.UDisks.Device')
  if not props['DeviceIsMounted']:
    if udi in active.keys(): del active[udi]
    return
  type = props['DriveMedia']
  label = props['IdLabel']
  info = {
    'udi': udi,
    'upi': '/org/mediauto/Mediauto/Process/' + type + '/' + label,
    'type': type,
    'device': props['DeviceFile'],
    'label': label,
    'size': props['PartitionSize']
  }
  queue_processes(udi, type, info)

def mediauto_queue_processor():

  global running_queue, processor_queue

  # Remove completed processes.
  new_running_queue = []
  for (processor, process) in running_queue:
    if process.isAlive():
      manager.PercentComplete(process.type(), process.upi(), process.progress())
      new_running_queue.append((processor, process))
    else:
      manager.ProcessEnded(process.type(), process.upi())
      processor.finish(process)
  running_queue = new_running_queue

  # Remove completed processors.
  processor_queue = [ x for x in processor_queue if x.count() > 0 ]
  
  # See if there's anything new to process.
  for processor in processor_queue:
    if len(running_queue) < MAX_PROCESSES:
      processtype = processor.select()
      if processtype:
        process = processor.get(processtype)
        running_queue.append((processor, process))
        manager.ProcessStarted(process.type(), process.upi())
        processor.start(processtype)

  return True

# Main daemon routine.
if __name__ == '__main__':

  # CENTOS 5
  try:
    bus.add_signal_receiver(
      hal_device_insert,
      'DeviceAdded',
      'org.freedesktop.Hal.Manager',
      'org.freedesktop.Hal',
      '/org/freedesktop/Hal/Manager'
    )
  except: pass

  # CENTOS 5
  try:
    bus.add_signal_receiver(
      hal_device_remove,
      'DeviceRemoved',
      'org.freedesktop.Hal.Manager',
      'org.freedesktop.Hal',
      '/org/freedesktop/Hal/Manager'
    )
  except: pass

  # Ubuntu 11.04
  try:
    bus.add_signal_receiver(
      udisks_device_changed,
      'DeviceChanged',
      None,
      'org.freedesktop.UDisks',
      '/org/freedesktop/UDisks'
    )
  except: pass

  # Run forever.
  gobject.timeout_add(int(mediauto.config.variable('mainloop.delay')), mediauto_queue_processor)
  gobject.MainLoop().run()
