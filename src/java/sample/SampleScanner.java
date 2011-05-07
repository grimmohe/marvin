package sample;

import java.awt.image.Raster;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import au.edu.jcu.v4l4j.CaptureCallback;
import au.edu.jcu.v4l4j.VideoFrame;
import au.edu.jcu.v4l4j.exceptions.V4L4JException;

/**
 * Scannt die Spalten eines Frames nach der besten Lichtquelle für die Distanzbestimmung
 */
public class SampleScanner implements CaptureCallback {

	private SampleUpdate updater;
	private float[] columnThreshold;

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

		int minY = raster.getMinY();
		int width = raster.getWidth();
		int height = raster.getHeight();

		if (columnThreshold.length != width) columnThreshold = new float[width];

		for (int column = raster.getMinX(); column < width; column++) {
			ColumnScanResult scanResult = scanColumn
											(columnThreshold[column],
											 raster.getPixels(column, minY, 1, height, (int[]) null));
			if (scanResult.getSample() != null) {
				sampleList.add(scanResult.getSample());
			}

			columnThreshold[column] = scanResult.getNewThreshold();
		}

		return sampleList;
	}

	private ColumnScanResult scanColumn(float threshold, int[] pixels) {
		int lightSum = 0;
		int openCount = 0;
		int sampleRowSum = 0;
		int sampleLight = 0;

		List<Sample> samples = new ArrayList<Sample>();
		Sample sample = null;

		for (int row = 0; row < pixels.length; row++) {
			int light = pixels[row];
			lightSum += light;

			if (light > threshold) {
				openCount++;
				sampleRowSum += row;
				sampleLight += light * row;
			} else if (openCount > 0) {
				samples.add(new Sample(sampleLight / sampleRowSum, sampleLight / openCount));

				openCount = 0;
				sampleRowSum = 0;
				sampleLight = 0;
			}
		}

		Collections.sort(samples);

		if (samples.size() > 0) {
			sample = samples.get(0);
		}
		if (samples.size() > 1
				&& Math.min(sample.getRow(), pixels.length - sample.getRow())
					> Math.min(samples.get(1).getRow(), pixels.length - samples.get(1).getRow()))
		{
			sample = samples.get(1);
		}

		return new ColumnScanResult(lightSum / pixels.length, sample);
	}

	public SampleUpdate getUpdater() {
		return updater;
	}

}

class ColumnScanResult {

	private float newThreshold;
	private Sample sample;

	public ColumnScanResult(float newThreshold, Sample sample) {
		super();
		this.newThreshold = newThreshold;
		this.sample = sample;
	}

	public float getNewThreshold() {
		return newThreshold;
	}

	public Sample getSample() {
		return sample;
	}
}
