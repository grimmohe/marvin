package org.cbase.marvin.log;

import java.util.List;

import org.cbase.marvin.sample.Sample;
import org.cbase.marvin.video.Format;


public interface ClientLoggerCallback {

	public void newSampleList(List<Sample> samples);

	public void newNodeList(List<Sample> nodes);

	public void newRawImage(Format format);

	public void newRowNodes(List<Sample> deserializeSampleList);

}
