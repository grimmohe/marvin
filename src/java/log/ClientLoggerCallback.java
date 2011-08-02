package log;

import java.util.List;

import sample.RawImageData;
import sample.Sample;

public interface ClientLoggerCallback {

	public void newSampleList(List<Sample> samples);

	public void newNodeList(List<Sample> nodes);

	public void newRawImage(RawImageData deserializeRawImage);

	public void newRowNodes(List<Sample> deserializeSampleList);

}
