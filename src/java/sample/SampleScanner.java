package sample;

import java.awt.image.Raster;
import java.util.List;

import log.Logger;
import map.ScanMap;
import au.edu.jcu.v4l4j.CaptureCallback;
import au.edu.jcu.v4l4j.VideoFrame;
import au.edu.jcu.v4l4j.exceptions.V4L4JException;
import conf.Configuration;

/**
 * Scannt die Spalten eines Frames nach der besten Lichtquelle für die Distanzbestimmung
 */
public class SampleScanner implements CaptureCallback {

	private SampleUpdate updater;
	private Logger logger;
	private SampleParserGrimm sampleParser = new SampleParserGrimm();
	private boolean working = false;
	private SampleShrinker sampleShrinker = new SampleShrinker();


	public SampleScanner(SampleUpdate updater, Logger logger) {
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

			List<Sample> sampleList = sampleParser.generateSamples(frame);
			sampleList = calculateDistances(sampleList, frame);

			this.logger.logSampleList(sampleList);
			
			sampleShrinker.adapt(sampleList);
			sampleList = sampleShrinker.getSampleList();
			
			this.logger.logNodeList(sampleList);

			ScanMap sm = new ScanMap();
			sm.read(sampleList);

			this.updater.update(sm);

			this.working = false;
		}

		frame.recycle();
	}

	private List<Sample> calculateDistances(List<Sample> samples, VideoFrame frame) {

		Raster raster = frame.getRaster();
		float frameWidth = raster.getWidth();
		float frameHeight = raster.getHeight();
		float halfAngle = 90F - (Configuration.videoVAngle / 2);
	    float degreePerRow = (float)Configuration.videoVAngle/raster.getHeight();
	    double camRecessed = Configuration.videoLaserDistance * Math.tan(Math.toRadians(halfAngle));

		for (Sample sample : samples) {
			sample.setAngle(180 / frameWidth * sample.getColumn());

			float row = sample.getRow();
			if (row > frameHeight/2) {
				row = frameHeight - row;
			}

			float angle = halfAngle + row * degreePerRow;
			double distance = Configuration.videoLaserDistance * Math.tan(Math.toRadians(angle)) - camRecessed;

			sample.setDistance((float) distance);
		}
		return samples;

	}

	public SampleUpdate getUpdater() {
		return updater;
	}

}
