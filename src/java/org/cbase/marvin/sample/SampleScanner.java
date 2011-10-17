package org.cbase.marvin.sample;

import java.awt.image.Raster;
import java.util.List;

import org.cbase.marvin.conf.Configuration;
import org.cbase.marvin.log.LoggerServer;
import org.cbase.marvin.map.ScanMap;

import au.edu.jcu.v4l4j.CaptureCallback;
import au.edu.jcu.v4l4j.VideoFrame;
import au.edu.jcu.v4l4j.exceptions.V4L4JException;

/**
 * Scannt die Spalten eines Frames nach der besten Lichtquelle für die Distanzbestimmung
 */
public class SampleScanner implements CaptureCallback {

	private SampleUpdate updater;
	private LoggerServer logger;
	private SampleParser sampleParser = new SampleParserGrimm();
	private boolean working = false;
	private SampleShrinker sampleShrinker = new SampleShrinker();


	public SampleScanner(SampleUpdate updater, LoggerServer logger) {
		this.updater = updater;
		this.logger = logger;
	}

	public void exceptionReceived(V4L4JException e) {

		System.out.println("CaptureException occured: " + e.getMessage());
		e.printStackTrace();

	}

	public void nextFrame(VideoFrame frame) {

		if (!this.working) {
			this.working = true;

			logger.logRawImage(frame);

			List<Sample> sampleList = sampleParser.generateSamples(frame);
			sampleList = calculateDistances(sampleList, frame);

			this.logger.logSampleList(sampleList);

			List<Sample> shrinkedSampleList = sampleShrinker.adapt(sampleList);

			shrinkedSampleList = calculateDistances(shrinkedSampleList, frame);

			this.logger.logNodeList(shrinkedSampleList);

			if(shrinkedSampleList.size() > 0) {
				ScanMap sm = new ScanMap();
				sm.read(shrinkedSampleList);

				this.updater.update(sm);
			}

			this.working = false;
		}

		frame.recycle();
	}

	private List<Sample> calculateDistances(List<Sample> samples, VideoFrame frame) {

		Raster raster = frame.getRaster();
		float frameWidth = raster.getWidth();
		float frameHeight = raster.getHeight();
		Configuration conf = Configuration.getInstance();
		float halfAngle = 90F - (conf.videoVAngle / 2); // von gerade runter bis zum beginn des Bildes
	    float degreePerRow = (float)conf.videoVAngle / raster.getHeight();
	    float degreePerCol = conf.videoViewVAngle / frameWidth;

		for (Sample sample : samples) {
			sample.setAngle((degreePerCol * sample.getColumn()) - conf.videoViewVAngle / 2); // "-" um die linke Hälfte negativ zu bekommen

			float row = sample.getRow();
			if (row > frameHeight/2) { // alles auf die obere Hälfte
				row = frameHeight - row;
			}

			double angle = halfAngle + row * degreePerRow;
			double distance = conf.videoLaserDistance * Math.tan(Math.toRadians(angle));
			distance /= Math.cos(Math.toRadians(sample.getAngle()));
			sample.setDistance((float) distance);
		}

		return samples;
	}

	public SampleUpdate getUpdater() {
		return updater;
	}

}
