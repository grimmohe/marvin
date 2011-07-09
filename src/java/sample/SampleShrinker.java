package sample;

import java.util.ArrayList;
import java.util.List;

public class SampleShrinker {

	private final List<Sample> sampleList;

	public SampleShrinker(List<Sample> sampleList) {
		super();
		this.sampleList = sampleList;
	}

	public void shrink() {

		List<Sample> sampleListCopy = new ArrayList<Sample>();
		sampleListCopy.addAll(sampleList);

		float previousDiff=0;
		Sample previous=null;
		for (Sample sample : sampleListCopy) {
			if(previous != null) {
				float diff = sample.getRow() - previous.getRow();
				if(previousDiff != diff && (diff > 1 || diff < 1) ) {
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
	}

	public List<Sample> getSampleList() {
		return sampleList;
	}

}
