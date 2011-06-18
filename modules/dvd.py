#!/usr/bin/env python

import os
import re
import time
import stat
import tempfile
import subprocess

import mediauto.module
import mediauto.config
import mediauto.process

class DVDException(Exception):
  def __init__(self, message): Exception.__init__(self, message)

# TODO: real logs.
def log(msg):
  print msg

def normalize_dvd_title(title):
  return title.replace('_', ' ').title()

class DVDFetchInfoProcess(mediauto.process.MediautoProcess):
  def __init__(self, info):
    self.info = info
    mediauto.process.MediautoProcess.__init__(self, info['upi'] + '/' + self.type())
  def type(self): return 'dvd.info'
  def run(self):
    self.info['files'] = []
    self.info['titlesets'] = {}
    if not mediauto.config.program_enabled('dvdbackup'):
      # TODO: print warning about dvdbackup not being enabled
      return
    cmd = [
      mediauto.config.program_path('dvdbackup'),
      '--input', self.info['device'], '--info'
    ]
    in_filescan_mode = 0
    in_tsscan_mode = 0
    current_titleset = 0
    basedir = None
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, close_fds=True)
    line = p.stdout.readline()
    while line:
      main_ts = re.match('^\s+Title set containing the main feature is ([0-9]+)$', line)
      if main_ts != None:
        self.info['main_titleset'] = int(main_ts.group(1))
        line = p.stdout.readline() # Read next line.
        continue
      elif re.match('^File Structure DVD$', line) != None:
        in_filescan_mode = 1
        line = p.stdout.readline() # Read next line.
        continue
      elif re.match('^Title Sets:$', line) != None:
        in_tsscan_mode = 1
        line = p.stdout.readline() # Read next line.
        continue
      elif line.strip() == '':
        in_filescan_mode = 0
        line = p.stdout.readline() # Read next line.
        continue
      else:
        if in_tsscan_mode:
          ts = re.match('^\s+Title set ([0-9]+)$', line)
          aspect = re.match('^\s+The aspect ratio of title set ([0-9]+) is ([0-9]+\:[0-9]+)$', line)
          angles = re.search('^\s+Title set ([0-9]+) has ([0-9]+) angle', line)
          audio = re.search('^\s+Title set ([0-9]+) has ([0-9]+) audio track', line)
          subpicture = re.search('^\s+Title set ([0-9]+) has ([0-9]+) subpicture channel', line)
          chapters = re.search('^\s+Title ([0-9]+) has ([0-9]+) chapter', line)
          audiochannels = re.search('^\s+Title ([0-9]+) has ([0-9]+) audio channel', line)
          if ts:
            current_titleset = int(ts.group(1))
            self.info['titlesets'][current_titleset] = {}
          elif aspect:
            self.info['titlesets'][current_titleset]['aspect'] = aspect.group(2)
          elif angles:
            nangles = int(angles.group(2))
            self.info['titlesets'][current_titleset]['angles'] = nangles
            self.info['titlesets'][current_titleset]['titles'] = {}
          elif audio:
            self.info['titlesets'][current_titleset]['audiotracks'] = int(audio.group(2))
          elif subpicture:
            self.info['titlesets'][current_titleset]['subpicture_channels'] = int(subpicture.group(2))
          elif chapters:
            titlenum = int(chapters.group(1))
            self.info['titlesets'][current_titleset]['titles'][titlenum] = {}
            self.info['titlesets'][current_titleset]['titles'][titlenum]['chapters'] = int(chapters.group(2))
          elif audiochannels:
            self.info['titlesets'][current_titleset]['titles'][int(audiochannels.group(1))]['audio_channels'] = int(audiochannels.group(2))
        elif in_filescan_mode:
          if re.match('^\w+\/$', line) != None:
            basedir = line.strip()
          else:
            m = re.search('(\w+\.\w+)\s+(\w+)\s+(\w+)', line)
            filename = m.group(1)
            file = os.path.join(basedir, filename)
            size = int(m.group(2))
            self.info['files'].append( (file,size) )
      line = p.stdout.readline() # Read next line.
    p.stdout.close()

class DVDCopyProcess(mediauto.process.MediautoProcess):
  def __init__(self, info):
    self.info = info
    mediauto.process.MediautoProcess.__init__(self, info['upi'] + '/' + self.type())
  def type(self): return 'dvd.copy'
  def depends(self): return [ 'dvd.info' ]
  def run(self):
    """ Copy the DVD into the temporary directory info['tempdir']. """
    if not mediauto.config.program_enabled('dvdbackup'):
      raise DVDException("DVDBackup not found, cannot copy DVD.")
    # Run `dvdcopy`.
    cmd = [
      mediauto.config.program_path('dvdbackup'),
      '--input',  self.info['device'],
      '--output', self.info['tempdir'],
      '--name', self.info['label'], '-M'
    ]
    #log('exec: ' + str(cmd))
    proc = subprocess.Popen(cmd)
    # Track progress of the `dvdbackup` run.
    lastsize = 0
    expectedsize = 0
    while proc.poll() == None:
      expectedsize = 0 # How many bytes DVDInfo told us we should have.
      actualsize = 0 # How many bytes we actually have.
      for filename,size in self.info['files']:
        expectedsize += size # Increment from array data.
        testfile = os.path.join(self.info['rootdir'], filename)
        if not os.path.isfile(testfile): continue # Doesn't exist yet, zero size.
        actualsize += os.stat(testfile)[stat.ST_SIZE] # Increment from stat.
      if expectedsize == 0: completed = 0.0 # Don't divide by zero.
      else: completed = float(actualsize) / float(expectedsize)
      if lastsize != 0:
        sizesincelast = actualsize - lastsize
        self.set_speed('%.3f MB/s' % (sizesincelast / 1024000.0 / 5.05))
      lastsize = actualsize
      self.set_progress(completed)
      time.sleep(5)
    self.set_progress(1.0)

class DVDEjectProcess(mediauto.process.MediautoProcess):
  def __init__(self, info):
    self.info = info
    mediauto.process.MediautoProcess.__init__(self, info['upi'] + '/' + self.type())
  def type(self): return 'dvd.eject'
  def depends(self): return [ 'dvd.copy' ]
  def run(self):
    if not mediauto.config.program_enabled('eject'):
      raise DVDException("Eject not found, cannot eject DVD.")
    cmd = [ mediauto.config.program_path('eject'), self.info['device'] ]
    #log(str(cmd))
    subprocess.Popen(cmd).wait()
    self.set_progress(1.0)

class DVDISOProcess(mediauto.process.MediautoProcess):
  def __init__(self, info):
    self.info = info
    mediauto.process.MediautoProcess.__init__(self, info['upi'] + '/' + self.type())
  def type(self): return 'dvd.iso'
  def depends(self): return [ 'dvd.copy' ]
  def run(self):
    if not mediauto.config.program_enabled('mkisofs'):
      raise DVDException("mkisofs not found, cannot create ISO for DVD.")
    # Run `mkisofs`.
    cmd = [
      mediauto.config.program_path('mkisofs'),
      '-dvd-video',
      '-udf',
      '-o', self.info['destfile'],
      self.info['rootdir']
    ]
    #log(str(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Track progress of the `mkisofs` run.
    line = proc.stdout.readline() # Read first line.
    while line:
      isomatch = re.match('^\s*([0-9]+\.[0-9]+)\% done, estimate finish (.*)\s*$', line)
      if isomatch != None:
        est_date = isomatch.group(2)
        # TODO: set_eta() to a unix timestamp made from est_date
        self.set_progress(float(isomatch.group(1)) / 100.0)

      line = proc.stdout.readline() # Read next line.
    proc.stdout.close()
    self.set_progress(1.0)

class DVDCleanProcess(mediauto.process.MediautoProcess):
  def __init__(self, info):
    self.info = info
    mediauto.process.MediautoProcess.__init__(self, info['upi'] + '/' + self.type())
  def type(self): return 'dvd.clean'
  def depends(self): return [ 'dvd.iso' ]
  def run(self):
    """ Recursively delete the temporary directory. """

    # Run `rm`
    for x in [ '/', '/usr', '/var', '/tmp', '/etc', '/home', '/boot' ]:
      # TODO: safety check more directories, places that should never be deleted.
      if os.path.abspath(self.info['tempdir']) == os.path.abspath(x):
        raise Exception('DVD.clean() failed, attempt to remove system directory "%s" denied.')
    cmd = [ '/bin/rm', '-fr', self.info['tempdir'] ]
    #log(str(cmd))
    proc = subprocess.Popen(cmd)

    # Track progress of the `rm` run.
    while proc.poll() == None:
      expectedsize = 0 # How many bytes DVDInfo told us we should have.
      actualsize = 0 # How many bytes we actually have.
      for filename,size in self.info['files']:
        expectedsize += size # Increment from array data.
        testfile = os.path.join(self.info['rootdir'], filename)
        if not os.path.isfile(testfile): continue # Doesn't exist yet, zero size.
        actualsize += os.stat(testfile)[stat.ST_SIZE] # Increment from stat.
      if expectedsize == 0: completed = 1.0 # Don't divide by zero.
      else: completed = float(actualsize) / float(expectedsize)
      completed = 1.0 - completed
      self.set_progress(completed)
      time.sleep(5)
    self.set_progress(1.0)

class DVD(mediauto.process.MediautoProcessor):
  def __init__(self, info):
    mediauto.process.MediautoProcessor.__init__(self)
    # TODO: improve file name.
    if info['label'] != None: info['destfilename'] = normalize_dvd_title(info['label']) + '.iso'
    else: info['destfilename'] = 'UNKNOWN_DISC.iso'
    info['destfile'] = os.path.join(mediauto.config.variable('dvd.destination'), info['destfilename'])
    info['tempdir'] = tempfile.mkdtemp()
    info['rootdir'] = os.path.join(info['tempdir'], info['label'])
    self.declare(DVDFetchInfoProcess(info))
    self.declare(DVDCopyProcess(info))
    self.declare(DVDEjectProcess(info))
    self.declare(DVDISOProcess(info))
    self.declare(DVDCleanProcess(info))
    os.system('killall totem') # Hax.

mediauto.module.processor_register('dvd_rom', DVD)
mediauto.module.processor_register('optical_dvd', DVD)

