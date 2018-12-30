###################################
# Continuous hi-hat controller v0.1
#
# A python script for mididings.
# This code is public domain.
#
# 2012-12-22 Simone Baracchi
###################################

from mididings import *
from mididings.engine import *
from mididings.event import *
from time import time

#### Hi-hat parameters ####

# Full closed hihat(s). 
# These are the notes issued when the hi-hat is fully closed.
# The number of items should match the number of zones your hi-hat controller has.
hihats_base = [ 37 ]

# Pedal pressure ranges.
# Uses first sample (fully closed) if pedal is pushed more than 85 (e.g. first value here);
# second sample (slightly less closed) if pedal is pushed more than 35; etc
# The number of items must match the number of samples per hi-hat
hihats_pedal_range = [ 85, 35, 20, 10, 5, 1, 0 ]

# Mutes the hi-hat when the pedal is pushed more than the first value.
# The hi-hat must be opened again more than the second value to trigger other note-offs
hihats_noteoff_range = [ 30, 20 ]

# Samples to be muted when issuing a note-off.
# Sounds better if you stop only the more open hi-hats.
hihats_noteoff_notes = [ 39, 40, 41, 42, 43,    46, 47, 48, 49, 50 ]

# Sends a noteoff after a note hasn't been played for <noteoff_interval> seconds
noteoff_interval = 4

#### end of hi-hat parameters ####

class HiHatController:
    def __init__(self):
        self.pedal = -1
        self.open = 1;
        self.close = 0;
        self.notes = {}
        print "Starting..."
    def __call__(self, ev):
	global hihats_base, hihats_pedal_range, hihats_noteoff_range, hihats_noteoff_notes, noteoff_interval
        if ev.type_ == CTRL and ev.param == 4:
            self.pedal = ev.value
            print "hh: pedal ", self.pedal
            if (ev.value < hihats_noteoff_range[1]):
                self.open = 1
                self.close = 0
            elif (ev.value >= hihats_noteoff_range[0]):
                self.close = 1
            if (self.open == 1) and (self.close == 1):
                self.open = 0
                self.close = 0
                print "hh: stop everything!"
		queue = []
		for note in hihats_noteoff_notes:
                    queue.append(NoteOffEvent(ev.port, ev.channel, note, 127))
                return queue
            return None
        elif (ev.type_ == NOTEON) and (ev.note in hihats_base) and (self.pedal != -1):
            var = ev.note
            for range in hihats_pedal_range:
                if(self.pedal < range):
                    ev.note += 1
            print "hh: in=", var, " out=", ev.note

        # check for noteoffs
	self.notes[ev.note] = time()
	res = []
        for note,t in self.notes.iteritems():
            if ((time() - t) > noteoff_interval):
                res.append(NoteOffEvent(ev.port, ev.channel, note, 127))
                print "stale: ", note
        for note in res:
            del self.notes[note.note]
        res.append(ev)
        return res

run([
        Filter(NOTEOFF) >> Discard(),
        Filter(NOTEON|CTRL) >> Process(HiHatController()),
	Filter(AFTERTOUCH|POLY_AFTERTOUCH) >> VelocityFilter(0) >> NoteOff(EVENT_NOTE, 0),
    ] >> Velocity(gamma=0.75)
)