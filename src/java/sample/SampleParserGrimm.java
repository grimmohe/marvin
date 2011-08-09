package sample;

import java.awt.image.Raster;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import au.edu.jcu.v4l4j.VideoFrame;
import conf.Configuration;

public class SampleParserGrimm implements SampleParser {

	private float[] columnThreshold;

	/* (non-Javadoc)
	 * @see sample.SampleParser#generateSamples(au.edu.jcu.v4l4j.VideoFrame)
	 */
	public List<Sample> generateSamples(VideoFrame frame) {

		List<Sample> sampleList = new ArrayList<Sample>();

		Raster raster = frame.getRaster();

		int minY = raster.getMinY();
		int width = raster.getWidth();
		int height = raster.getHeight();

		if (columnThreshold == null || columnThreshold.length != width) columnThreshold = new float[width];

		float lastRow=0;
		for (int column = raster.getMinX(); column < width; column++) {
			ColumnScanResult scanResult = scanColumn
											(this.getThreshold(columnThreshold, column),
											 raster.getPixels(column, minY, 1, height, (int[]) null), (int) lastRow);
			if (scanResult.getSample() != null) {
				Sample sample = scanResult.getSample();
				sample.setColumn(column);
				sampleList.add(sample);
				lastRow = sample.getRow();
			}

			columnThreshold[column] = scanResult.getNewThreshold();
		}

		return sampleList;
	}

	private float getThreshold(float[] pixels, int index) {
		index = Math.min(Math.max(index, 2), pixels.length - 3);

		return (pixels[Math.max(0, index-2)]
		            + pixels[Math.max(0, index-1)]
				 	+ pixels[index]
					+ pixels[Math.min(index+1, pixels.length-1)]
					+ pixels[Math.min(index+2, pixels.length-1)]) / 5;
	}

	private ColumnScanResult scanColumn(float threshold, int[] pixels, int lastRow) {
		int lightSum = 0;
		int lightMax = 0;
		int openCount = 0;
		float sampleRowSum = 0;
		int sampleLight = 0;

		List<Sample> samples = new ArrayList<Sample>();
		Sample sample = null;

		int rowMin = 0;
		int rowMax = pixels.length;

		if (!Configuration.useTopLaser) rowMin = rowMax / 3 / 2 * 3;
		if (!Configuration.useBottomLaser) rowMax = rowMax / 3 / 2 * 3;

		for (int row = rowMin; row < rowMax; row+=3) {
			int light = Math.max(0, pixels[row] - (pixels[row+1] + pixels[row+2]) / 2);
			lightSum += light;
			lightMax = Math.max(lightMax, light);

			if (light > threshold) {
				openCount++;
				sampleRowSum += row / 3;
				sampleLight += light;
			} else if (openCount > 0 && sampleRowSum > 0) {
				float estrow = sampleRowSum / openCount;
				if (estrow > pixels.length / 6) {
					estrow = pixels.length / 3 - estrow;
				}
				samples.add(new Sample(estrow, sampleLight / openCount));

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

		return new ColumnScanResult((lightSum / pixels.length + lightMax) / 2, sample);
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
