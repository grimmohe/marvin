package sample;

import java.awt.image.Raster;
import java.util.List;

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
	private SampleParserGrimm sampleParser = new SampleParserGrimm();
	private boolean working = false;

	public SampleScanner(SampleUpdate updater) {
		this.updater = updater;
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

			new SampleShrinker(sampleList).shrink();

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
		float halfAngle = (Configuration.videoVAngle / 2);
	    float degreePerRow = Configuration.videoVAngle/raster.getHeight();
	    double camRecessed = Configuration.videoLaserDistance / Math.tan(halfAngle);

		for (Sample sample : samples) {
			sample.setAngle(180 / frameWidth * sample.getColumn());

			float row = sample.getRow();
			if (row > frameHeight/2) {
				row = frameHeight - row;
			}

			float angle = 90 - row * degreePerRow;
			double distance = Configuration.videoLaserDistance / Math.tan(angle) - camRecessed;

			sample.setDistance((float) distance);
		}
		return samples;

	}

	public SampleUpdate getUpdater() {
		return updater;
	}

}
