package log;

import java.util.List;

import sample.RawImageData;
import sample.Sample;

public class NullClientLoggerCallback implements ClientLoggerCallback {

	@Override
	public void newNodeList(List<Sample> nodes) {
		System.out.println("ClientLoggerCallback: newNodeList");
	}

	@Override
	public void newRawImage(RawImageData deserializeRawImage) {
		System.out.println("ClientLoggerCallback: newRawImage");
	}

	@Override
	public void newRowNodes(List<Sample> deserializeSampleList) {
		System.out.println("ClientLoggerCallback: newRowNodes");
	}

	@Override
	public void newSampleList(List<Sample> samples) {
		System.out.println("ClientLoggerCallback: newSampleList");
	}

}
