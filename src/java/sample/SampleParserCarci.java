package sample;

import java.util.ArrayList;
import java.util.List;

public class SampleParserCarci {

	private List<int[]> rgbList;

	public SampleParserCarci(List<int[]> rgbList) {
		super();
		this.rgbList = rgbList;
	}
	
	public List<Sample> generateSamples() {
		
		int range = rgbList.size();
		List<int[]> hotspots = findHotspots();
		
		int pages = range/hotspots.size();
		
		return new ArrayList<Sample>();
		
	}
	
	private List<int[]> findHotspots() {
		
		List<int[]> hotspots = new ArrayList<int[]>();
		int lastHeight=0;
		for (int i=0; rgbList.size() > i; i++) {
			int[] rgb = rgbList.get(i);
			int curr = rgb[0] + rgb[1] + rgb[2];
			
			if(curr > lastHeight) {
				lastHeight = curr;
			} else if (curr < lastHeight) {
				hotspots.add(new int[] {i});
			}
		}
		
		return hotspots;
	}
	
}
