package sample;

import java.awt.image.Raster;
import java.util.ArrayList;
import java.util.List;

import au.edu.jcu.v4l4j.CaptureCallback;
import au.edu.jcu.v4l4j.VideoFrame;
import au.edu.jcu.v4l4j.exceptions.V4L4JException;

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

		List<Sample> sampleList = new ArrayList<Sample>();

		Raster raster = frame.getRaster();

		int[] rgb = raster.getPixel(0, 0, (int[]) null);

		System.out.println(rgb[0] + "," + rgb[1] + "," + rgb[2]);

		return sampleList;
	}

	public SampleUpdate getUpdater() {
		return updater;
	}

}
