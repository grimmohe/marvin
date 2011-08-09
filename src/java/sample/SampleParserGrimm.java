package sample;

import java.awt.image.Raster;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import conf.Configuration;

import au.edu.jcu.v4l4j.VideoFrame;

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
											(columnThreshold[column],
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

	private ColumnScanResult scanColumn(float threshold, int[] pixels, int lastRow) {
		int lightSum = 0;
		int openCount = 0;
		float sampleRowSum = 0;
		int sampleLight = 0;

		List<Sample> samples = new ArrayList<Sample>();
		Sample sample = null;

		int rowMin = 0;
		int rowMax = pixels.length;

		if (!Configuration.useTopLaser) rowMin = rowMax / 3 / 2 * 3;
		if (!Configuration.useBottomLaser) rowMax = rowMax / 3 / 2 * 3;
		
//		rowMin = Math.max(0, Math.min(rowMin, lastRow - 25));
//		rowMax = Math.min(rowMax, lastRow + 25);
		
//		System.out.println("rowMin:"+rowMin+", rowMax:"+rowMax);
		for (int row = rowMin; row < rowMax; row+=3) {
			int light = Math.max(0, pixels[row] - pixels[row+1] - pixels[row+2]);
//			int light = pixels[row] - pixels[row+1] - pixels[row+2];
			lightSum += light;	
//			System.out.print("#:"+row);
//			System.out.print("r:"+pixels[row]);
//			System.out.print("g:"+pixels[row+1]);
//			System.out.println("b:"+pixels[row+2]);

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
//				break;
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
//			System.out.println(samples.size());
			sample = samples.get(1);
		}

		return new ColumnScanResult(lightSum / pixels.length, sample);
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
