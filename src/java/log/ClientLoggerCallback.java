package log;

import java.util.List;

import sample.Sample;

public interface ClientLoggerCallback {

	public void newSampleList(List<Sample> samples);

	public void newNodeList(List<Sample> nodes);

}
