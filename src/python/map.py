#coding=utf8

import math

"""
import sqlite3
connection = sqlite3.connect(":memory:")
"""
from dbus.decorators import method

__marker = [(0,0), (5,0), (5,1), (6,1), (6,6), (0,6)]

class Distance :
    def __init__(self, distance, connected):
        self.distance = distance
        self.connected = connected

class Mark :
    def __init__(self, id, distance):
        self.id = id
        self.distance = distance

marker = []
distances = []

for ii in range(len(__marker)):
    for aa in range(ii+1, len(__marker)):
        d = Distance(math.sqrt(math.pow(__marker[ii][0] - __marker[aa][0], 2) + math.pow(__marker[ii][1] - __marker[aa][1], 2)),
                     abs(__marker.index(__marker[ii]) - __marker.index(__marker[aa])) == 1)
        distances.append(d)
        marker.append(Mark(__marker[ii], d))
        marker.append(Mark(__marker[aa], d))

def connected (d1, d2):
    for m1 in marker:
        if m1.distance == d1:
            for m2 in marker:
                if m2.id == m1.id and m2.distance == d2:
                    return True
    return False

samples = []

class Sample :
    def __init__(self, x, y):
        self.x = x
        self.y = y

samples.append(Sample(0, 0))
samples.append(Sample(5, 0))
samples.append(Sample(5, 1))
samples.append(Sample(6, 1))
samples.append(Sample(6, 6))

class SampleDistance :
    def __init__(self, s1, s2):
        self.samples = [s1, s2]
        self.distance = math.sqrt(math.pow(s1.x - s2.x, 2) + math.pow(s1.y - s2.y, 2))

sampleDistances = []

for ii in range(1, len(samples)):
    sampleDistances.append(SampleDistance(samples[ii-1], samples[ii]))

class Finding :
    def __init__(self):
        self.chain = []

findings = []

class Link :
    def __init__(self, sd, d):
        self.sampledist = sd
        self.distance = d

last = None
for index in range(len(sampleDistances)):
    sd = sampleDistances[index]
    distsSorted = sorted(distances, cmp=lambda d1, d2: int(abs(d1.distance - sd.distance) - abs(d2.distance - sd.distance)))

    for mapdist in distsSorted:
        if mapdist.distance != sd.distance: #hier die gewisse unschärfe
            break

        if last:
            for finding in findings:
                if (ii > 0
                    and finding.chain[len(finding.chain)-1].sampledist == last
                    and connected(finding.chain[len(finding.chain)-1].distance, mapdist)
                ):
                    copy = Finding()
                    copy.chain = sorted(finding.chain, cmp=lambda x, y: 0)
                    copy.chain.append(Link(sd, mapdist))
                    findings.append(copy)

        f = Finding()
        f.chain.append(Link(sd, mapdist))
        findings.append(f)

    last = sd

findings.sort(key=lambda x: len(x.chain), reverse=True)

print a

