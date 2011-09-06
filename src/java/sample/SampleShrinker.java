package sample;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class SampleShrinker {

	private List<Sample> sampleList = new ArrayList<Sample>();
	private final float TRESH_HOLD = 0.35F;
	private final float TRESH_HOLD_N = TRESH_HOLD * -1;
	private final int APPROXIMATE = 5;
	private List<List<Sample>> listList = new ArrayList<List<Sample>>();
	
	public SampleShrinker() {
		super();
	}

	public List<Sample> adapt(List<Sample> sampleList) {
		
		if(listList.size()>= APPROXIMATE) {
			listList.remove(0);
		}

		List<Sample> sampleListCopy = new ArrayList<Sample>();
		sampleListCopy.addAll(sampleList);
		
		listList.add(sampleListCopy);
		
		int minSize=listList.get(0).size();
		for (List<Sample> sampleList2 : listList) {
			minSize = Math.min(sampleList2.size(), minSize);
		}
		
		List<List<Sample>> tempApproxList = new ArrayList<List<Sample>>();
		for (List<Sample> sampleList2 : listList) {
			tempApproxList.add(resizeList(sampleList2, minSize));
		}

		List<Sample> tempSampleList = approximate(tempApproxList);
		
		List<Sample> shrinkedSampleList = shrink(tempSampleList);
		
//		System.out.println("adapt new list: lists: " + listList.size() + ", currListSize: " + shrinkedSampleList.size());
		
		return shrinkedSampleList;
		
	}
	
	private List<Sample> approximate(List<List<Sample>> lists) {
		
		int numLists = lists.size();
		int length = lists.get(0).size();
		List<Sample> approxList = new ArrayList<Sample>();
		for(int list=1; list<numLists; list++) {
			length = Math.min(length, lists.get(list).size());
		}
		for(int item=0;item<length && length > 0 && numLists > 0;item++) {
			float approxRow=0, approxIntensity=0, angle=0, distance=0;
			for(int list=0; list<numLists; list++) {
				List<Sample> list2 = lists.get(list);
				Sample sample = list2.get(item);
				approxRow += sample.getRow();
				approxIntensity += sample.getIntensity();
			}
			Sample approxSample = new Sample(approxRow/numLists, approxIntensity/numLists);
			approxSample.setColumn(item);
			approxSample.setAngle(angle/numLists);
			approxSample.setDistance(distance/numLists);
			approxList.add(approxSample);
		}
		return approxList;
		
	}

	private List<Sample> shrink(List<Sample> sampleList) {

		List<Sample> sampleListCopy = new ArrayList<Sample>();
		sampleListCopy.addAll(sampleList);

		float previousDiff=0;
		int removed=0;
		Sample previous=null;
		for (Sample sample : sampleListCopy) {
			if(previous != null) {
				float diff = sample.getRow() - previous.getRow();
//				float diffValue = (previousDiff - diff);
				if((diff < TRESH_HOLD ) && (diff > (TRESH_HOLD_N)) ) {
					sampleList.remove(previous);
					removed++;
				} else {
//					System.out.print(diff + ", ");
					previousDiff = diff;
				}
			}
			previous = sample;
		}
//		System.out.println("removed " + removed);

		// remove fist and last item
//		if(sampleList.size()>2) {
//			sampleList.remove(sampleList.get(0));
//			sampleList.remove(sampleList.get(sampleList.size()-1));
//		}
		
		return sampleList;
		
	}

	public List<Sample> getSampleList() {
		return sampleList;
	}

	public List<Sample> resizeList(List<Sample> samples, int newWidth) {
		int oldWidth = samples.size();
		Sample[] newSamples = new Sample[newWidth];
		
		if(oldWidth == newWidth || newWidth == 0) {
			return samples;
		}

//		System.out.println("resize from "+samples.size()+" to " + newWidth + "("+newSamples.length+")");
	    int x_ratio = (int)((oldWidth<<16)/newWidth)+1;
	    int x2 ;
        for (int j=0;j<newWidth;j++) {
            x2 = ((j*x_ratio)>>16) ;
            newSamples[j] = samples.get(x2);
        }                
        
        List<Sample> newSamplesList = new ArrayList<Sample>(Arrays.asList(newSamples));
		return newSamplesList;
	}	
	
}
