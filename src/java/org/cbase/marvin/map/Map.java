package org.cbase.marvin.map;

import java.util.ArrayList;
import java.util.List;

import org.cbase.marvin.map.Segment;
import org.cbase.marvin.map.Vertex;

public class Map {

	private List<Segment> segments = new ArrayList<Segment>();
	private List<Vertex> vertices = new ArrayList<Vertex>();

	public void addSegment(Segment s) {
		this.segments.add(s);
	}

	public void addVertex(Vertex v) {
		this.vertices.add(v);
	}

}
