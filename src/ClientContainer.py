#!/usr/bin/env python
#coding=utf8

import map
import xmltemplate
import threading
import callback as cb
import common

#TODO: commanding to move towards a wall when already touching it is bad
#TODO: the assignment structure is way too inflexible

class ClientContainer(threading.Thread):

    def __init__(self, clientConnection):
        threading.Thread.__init__(self)
        self.position = map.Position()
        self.xExtent = {"min": .0, "max":.0}
        self.yExtent = {"min": .0, "max":.0}
        self.map = map.Map()
        self.devs = {}
        self.clientConnection = clientConnection
        self.clientConnection.cbl["onDataIncoming"].add(cb.CallbackCall(self.clientReceiving))
        self.actionlogData = ""
        self.actionlogNew = threading.Event()
        self.stop = False
        self.cbMapRefresh = None
        self.template = xmltemplate.Template()
        self.start()

    def assimilateActions(self, actionlog):
        """ turn the cliens action log into a map and if send, get some other infos """

        self.moveStartPosition = None

        for action in actionlog.actions:
            # contains action and value
            dev, key = action.action.lower().split(":")

            if dev == "engine" and self.devs.has_key(dev):
                if key == "turned":
                    self.position.orientation += action.value
                    for dev in self.devs.values():
                        if dev.has_key("touch"):
                            dev["touch"] = False

                elif key == "distance":
                    newPos = self.position.getPointInDistance(action.value)

                    if ( self.devs.has_key("head")
                         and self.devs["head"].has_key("position")
                         and self.devs["head"]["position"] ):
                        for sdev in self.devs:
                            if self.devs[sdev].has_key("dimension") \
                            and self.devs[sdev]["dimension"]:
                                if self.devs[sdev].has_key("touch") \
                                and self.devs[sdev]["touch"] :
                                    sensorOffset = None
                                    if self.devs[sdev].has_key("orientation") \
                                    and self.devs[sdev].has_key("distance"):
                                        sensorOffset = self.devs[sdev]["orientation"].copy()
                                        sensorOffset.size.x *= self.devs[sdev]["distance"]
                                        sensorOffset.size.y *= self.devs[sdev]["distance"]
                                    # here the sensor vector is copied to start and end point of the movement
                                    v_start = self.devs[sdev]["dimension"].copy(map.Point(self.position.point.x, self.position.point.y),
                                                                                self.position.orientation,
                                                                                sensorOffset)
                                    v_end = self.devs[sdev]["dimension"].copy(newPos, self.position.orientation, sensorOffset)
                                    # point 1 start to end
                                    v1 = map.Vector().combine(v_start, v_end, map.Vector.START_POINT)
                                    # point 2 start to end
                                    v2 = map.Vector().combine(v_start, v_end, map.Vector.END_POINT)
                                    # the one on the outside wins
                                    if v_end.distanceMax(v1) > v_end.distanceMax(v2):
                                        self.map.borders.add(v1)
                                    else:
                                        self.map.borders.add(v2)
                                    # sensor on end position
                                    self.map.borders.add(v_end)
                    # finally accept the new position
                    self.position.point = newPos

            else:
                if not self.devs.has_key(dev):
                    self.devs[dev] = {}
                self.devs[dev][key] = action.value
                if key == "distance":
                    self.devs[dev]["touch"] = (action.value < 1.0)
                    if self.devs[dev]["touch"]:
                        sensorOffset = None
                        if self.devs[dev].has_key("orientation"):
                            sensorOffset = self.devs[dev]["orientation"].copy()
                            sensorOffset.size.x *= action.value
                            sensorOffset.size.y *= action.value
                        self.map.borders.add(self.devs[dev]["dimension"].copy(map.Point(self.position.point.x,
                                                                                        self.position.point.y),
                                                                              self.position.orientation,
                                                                              sensorOffset))
                elif key == "dimension":
                    x, y, size_x, size_y = action.value.split(";")
                    self.devs[dev][key] = map.Vector(map.Point(x, y), map.Point(size_x, size_y))
                    self.xExtent["min"] = min(self.xExtent["min"], self.devs[dev][key].getStartPoint().x, self.devs[dev][key].getEndPoint().x)
                    self.xExtent["max"] = max(self.xExtent["max"], self.devs[dev][key].getStartPoint().x, self.devs[dev][key].getEndPoint().x)
                    self.yExtent["min"] = min(self.yExtent["min"], self.devs[dev][key].getStartPoint().y, self.devs[dev][key].getEndPoint().y)
                    self.yExtent["max"] = max(self.yExtent["max"], self.devs[dev][key].getStartPoint().y, self.devs[dev][key].getEndPoint().y)
                elif key == "orientation":
                    size_x, size_y = action.value.split(";")
                    self.devs[dev][key] = map.Vector(map.Point(0, 0), map.Point(size_x, size_y))
                elif key in ("radius", "position"):
                    self.devs[dev][key] = float(action.value)

        self.map.merge()

        if self.cbMapRefresh:
            self.cbMapRefresh()


    def clientReceiving(self, attributes):
        self.actionlogData=attributes["data"]
        self.actionlogNew.set()

    def discover(self):
        """ discover new borders """
        if self.devs.has_key("self") and self.devs["self"].has_key("radius"):
            loose = self.map.borders.getLooseEnds(self.position)
            if loose and len(loose):
                loose = loose[0]
                vlen = loose.len()
                # the direction of vector 'loose' is the loose end to discover
                # with bmulti the target waypoint will be set 'radius' before the vectors end
                bmulti = min(vlen, self.devs["self"]["radius"]) / vlen
                self.map.addWaypoint(map.WayPoint(loose.point.x + loose.size.x - loose.size.x * bmulti,
                                                  loose.point.y + loose.size.y - loose.size.y * bmulti,
                                                  map.WayPoint.WP_FAST | map.WayPoint.WP_DISCOVER,
                                                  loose))
            elif self.map.borders.count() == 0:
                self.map.addWaypoint(map.WayPoint(self.position.point.x, self.position.point.y, map.WayPoint.WP_DISCOVER))
        else:
            self.clientConnection.log("try to discover, but no \"radius\" item found" )

    def getSensorList(self, extended=False):
        sensors = []
        for devname in self.devs:
            if self.devs[devname].has_key("dimension") \
            and self.devs[devname].has_key("distance") \
            and self.devs[devname].has_key("orientation") :
                if extended:
                    os = self.devs[devname]["orientation"]
                    os.size.x *= self.devs[devname]["distance"]
                    os.size.x *= self.devs[devname]["distance"]
                else: os = None
                s = self.devs[devname]["dimension"].copy(offset=os)
                s.name = devname
                sensors.append(s)
        return sensors

    def handlePanicEvents(self):
        """ in case the batterie is low or other stuff, handle that """
        if not self.devs.has_key("self") or not self.devs["self"].has_key("raduis"):
            pass
            #TODO: Oh, panic!(TM)

    def run(self):
        print "["+self.name+"] ClientContainer running..."
        while not self.stop:
            print "start wait"
            self.actionlogNew.clear()
            self.actionlogNew.wait()
            print "done wait"
            if not self.stop and self.actionlogData:
                actionlog = common.Actionlog()
                try:
                    actionlog.readXml(self.actionlogData)
                except:
                    print "no valid xml data?"
                self.assimilateActions(actionlog)
                self.handlePanicEvents()
                if not self.map.routeIsSet():
                    self.discover()
                if not self.map.routeIsSet():
                    self.fill()
                self.sendAssignments()
        print "ClientContainer: leaving event loop"

    def fill(self):
        """ yea... grimm, what to do here? self.map has no route, now FILLLLLL it! """
        pass

    def sendAssignments(self):
        """
        send assignments in a packed format back to our waiting client.
        there, xml-templates will be filled and executed.
        """
        pos = self.position.copy()
        if self.devs.has_key("self"):
            router = map.Router(self.devs["self"]["radius"])
            for wp in self.map.waypoints:
                if wp.duty & map.WayPoint.WP_FAST:
                    router.actionRoute(pos, wp, self.getSensorList, self.template.addTemplate, self.map.getCollisions)

                if wp.duty & map.WayPoint.WP_STRICT:
                    collisions = self.map.getCollisions(pos, self.getSensorList(True), 0)
                    for i in range(len(collisions)):
                        if pos.point.getDistanceTo(wp) < collisions[i][0]:
                            break
                    router.actionRoute(pos, collisions[i][2], self.getSensorList, self.template.addTemplate, self.map.getCollisions)
                    if i < len(collisions)-1:
                        bpos = map.Position(collisions[i+1][2], pos.orientation+180)
                        bc = self.map.getCollisions(bpos, self.getSensorList(True), 0)
                        if len(bc) and pos.point.getDistanceTo(wp) < bc[0][0]:
                            router.actionRoute(pos, bc[0][2], self.getSensorList, self.template.addTemplate, self.map.getCollisions)

                if wp.duty & map.WayPoint.WP_DISCOVER:
                    router.actionDiscover(pos, wp.attachment, cb_getSensorList=self.getSensorList, cb_addAction=self.template.addTemplate)

        xml = self.template.getTransmissionData()
        print "send: " + xml
        self.clientConnection.write(xml)
        self.map.clearWaypoints()
        self.template.clear()

    def shutdown(self):
        if self.clientConnection:
            self.clientConnection.disconnect(True)
        self.clientConnection = None
        self.actionlog = None
        # semi fire event to come out of wait state, but set stop flag before, so thread
        # is killed
        self.stop = True
        if self.actionlogNew:
            self.actionlogNew.set()
        self.actionlogNew = None
        self.map = None
