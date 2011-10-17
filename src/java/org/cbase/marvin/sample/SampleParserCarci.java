package org.cbase.marvin.sample;

import java.awt.image.Raster;
import java.util.ArrayList;
import java.util.List;

import au.edu.jcu.v4l4j.VideoFrame;

public class SampleParserCarci implements SampleParser {


	public SampleParserCarci(List<int[]> rgbList) {
		super();
	}

	public List<Sample> generateSamples(VideoFrame frame) {

		Raster raster = frame.getRaster();

		int minY = raster.getMinY();
		int width = raster.getWidth();
		int height = raster.getHeight();

		for (int column = raster.getMinX(); column < width; column++) {
			int[] rgbList = raster.getPixels(column, minY, 1, height, (int[]) null);
			int range = rgbList.length;
			List<int[]> hotspots = findHotspots(rgbList);

			int pages = range/hotspots.size();
		}

		return new ArrayList<Sample>();

	}

	private List<int[]> findHotspots(int[] rgbList) {

//		List<int[]> hotspots = new ArrayList<int[]>();
//		int lastHeight=0;
//		for (int i=0; rgbList.length > i; i++) {
//
//			int curr = rgb[i] + rgb[i+1] + rgb[i+2];
//
//			if(curr > lastHeight) {
//				lastHeight = curr;
//			} else if (curr < lastHeight) {
//				hotspots.add(new int[] {i});
//			}
//		}
//
//		return hotspots;
	return null;
	}

}
