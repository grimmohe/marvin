package sample;

import java.awt.image.Raster;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import conf.Configuration;

import au.edu.jcu.v4l4j.CaptureCallback;
import au.edu.jcu.v4l4j.VideoFrame;
import au.edu.jcu.v4l4j.exceptions.V4L4JException;

/**
 * Scannt die Spalten eines Frames nach der besten Lichtquelle für die Distanzbestimmung
 */
public class SampleScanner implements CaptureCallback {

	private SampleUpdate updater;

	public SampleScanner(SampleUpdate updater) {
		this.updater = updater;
	}

	public void exceptionReceived(V4L4JException e) {

		System.out.println("CaptureException occured: " + e.getMessage());
		e.printStackTrace();

	}

	public void nextFrame(VideoFrame frame) {

		List<Sample> sampleList = parseFrame(frame);
		frame.recycle();
		updater.update(sampleList);

	}

	private List<Sample> parseFrame(VideoFrame frame) {

		SampleParserGrimm sampleParser = new SampleParserGrimm();
		return calculateDistances(sampleParser.generateSamples(frame), frame);
		
	}
	
	private List<Sample> calculateDistances(List<Sample> samples, VideoFrame frame) {
		
		Raster raster = frame.getRaster();	
		float upperTrashhold = raster.getHeight()/2;
		float halfAngle = (Configuration.videoAngle / 2);
		
		for (Sample sample : samples) {
			float degreePerRow = halfAngle/upperTrashhold;
			if(sample.getRow() >= upperTrashhold) {
				float row = sample.getRow() - upperTrashhold;
				float degree = row*degreePerRow;
				degree = (halfAngle + degree) - 90;
				
			}
		}
		return samples;
		
	}

	public SampleUpdate getUpdater() {
		return updater;
	}
	
}
