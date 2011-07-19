package sample;

import java.util.ArrayList;
import java.util.List;

public class SampleShrinker {

	private List<Sample> sampleList = new ArrayList<Sample>();
	private final int TRESH_HOLD = 100;
	private final int APPROXIMATE = 5;
	private List<List<Sample>> listList = new ArrayList<List<Sample>>();
	
	public SampleShrinker() {
		super();
	}

	public void adapt(List<Sample> sampleList) {
		
		if(listList.size()>= APPROXIMATE) {
			listList.remove(0);
		}
		
		listList.add(sampleList);
		
		int minSize=listList.get(0).size();
		for (List<Sample> sampleList2 : listList) {
			minSize = Math.min(sampleList2.size(), minSize);
		}
//		System.out.println("minsize: " + minSize);
		
		for (List<Sample> sampleList2 : listList) {
			int removeNEntrie = sampleList2.size() % minSize;
			System.out.println("1: listSize: " + sampleList2.size() + ", minSize: " + minSize + ", removeNEntries: " + removeNEntrie);
			if(removeNEntrie>0 && sampleList2.size()>minSize)  {
				System.out.println("remove every: " + sampleList2.size()/removeNEntrie);
				System.out.println("remove every: " + sampleList2.size()%removeNEntrie);
				for(int i=sampleList2.size()-1;i>=0; i-=removeNEntrie) {
//					System.out.println("remove entrie " + i);
					sampleList2.remove(i);
				}
			}
			System.out.println("2: listSize: " + sampleList2.size() + ", minSize: " + minSize);
		}
		
		List<Sample> shrinkedSampleList = shrink(sampleList);
		this.sampleList = shrinkedSampleList;
		
	}
	
	private List<Sample> shrink(List<Sample> sampleList) {

		List<Sample> sampleListCopy = new ArrayList<Sample>();
		sampleListCopy.addAll(sampleList);

		float previousDiff=0;
		Sample previous=null;
		for (Sample sample : sampleListCopy) {
			if(previous != null) {
				float diff = sample.getRow() - previous.getRow();
				if(previousDiff != diff && (diff > TRESH_HOLD || diff < TRESH_HOLD) ) {
					previousDiff = diff;
				} else {
					sampleList.remove(previous);
				}
			}
			previous = sample;
		}

		// remove fist and last item
		if(sampleList.size()>2) {
			sampleList.remove(sampleList.get(0));
			sampleList.remove(sampleList.get(sampleList.size()-1));
		}
		
		return sampleList;
		
	}

	public List<Sample> getSampleList() {
		return sampleList;
	}

}
