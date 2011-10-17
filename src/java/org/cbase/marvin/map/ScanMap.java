package org.cbase.marvin.map;

import java.util.ArrayList;
import java.util.List;

import org.cbase.marvin.map.Map;
import org.cbase.marvin.sample.Sample;


public class ScanMap extends Map {

	public void read (List<Sample> sl) {

		List<ScanVertex> pastVertices = new ArrayList<ScanVertex>();

		for (Sample sample: sl) {
			ScanVertex vertex = new ScanVertex();
			vertex.pos = sample.getPosition();
			this.addVertex(vertex);

			for (ScanVertex pastVertex: pastVertices) {
				Segment seg = new Segment(vertex.getDistance(pastVertex));
				this.addSegment(seg);

				vertex.addSegment(seg);
				pastVertex.addSegment(seg);
			}
		}
	}

}
