package org.cbase.marvin.log;

import java.awt.image.BufferedImage;
import java.util.List;

import org.cbase.marvin.sample.Sample;


public interface ClientLoggerCallback {

	public void newSampleList(List<Sample> samples);

	public void newNodeList(List<Sample> nodes);

	public void newRawImage(BufferedImage deserializeRawImage);

	public void newRowNodes(List<Sample> deserializeSampleList);

}
