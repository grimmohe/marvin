package map;

import java.util.ArrayList;
import java.util.List;

public class Vertex {

	private List<Segment> segments = new ArrayList<Segment>();

	public void addSegment(Segment seg) {
		this.segments.add(seg);
	}

}
