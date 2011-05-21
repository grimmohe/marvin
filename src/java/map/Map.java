package map;

import java.util.ArrayList;
import java.util.List;

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
