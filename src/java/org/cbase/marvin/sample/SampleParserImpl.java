package org.cbase.marvin.sample;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.cbase.marvin.conf.Configuration;
import org.cbase.marvin.video.Format;

public class SampleParserImpl implements SampleParser {

	public SampleParserImpl() {
		super();
	}

	private float[] columnThreshold = new float[0];
	private Map<Integer, SampleCacheContainer> sampleCache = new HashMap<Integer, SampleCacheContainer>();
	private int frameCacheCount;

	/* (non-Javadoc)
	 * @see sample.SampleParser#generateSamples(au.edu.jcu.v4l4j.VideoFrame)
	 */
	public List<Sample> generateSamples(Format frame) {

		List<Sample> sampleList = new ArrayList<Sample>();

		int width = frame.getWidth();

		if (columnThreshold.length != width) columnThreshold = new float[width];

		float lastRow=0;
		for (int column = 0; column < width; column++) {
			ColumnScanResult scanResult = scanColumn
											(this.getThreshold(columnThreshold, column),
											 column, frame, (int) lastRow);
			if (scanResult.getSample() != null) {
				Sample sample = scanResult.getSample();
				sample.setColumn(column);
				sampleList.add(sample);
				lastRow = sample.getRow();
			}

			columnThreshold[column] = scanResult.getNewThreshold();
		}

		this.checkCache(sampleList);

		return sampleList;
	}

	private void checkCache(List<Sample> sampleList) {
		List<Sample> copy = new ArrayList<Sample>(sampleList);

		for (int run = 0; run < copy.size(); run++) {
			Sample s = copy.get(run);

			boolean valid = true;
			for (Map.Entry<Integer, SampleCacheContainer> scl: this.sampleCache.entrySet()) {
				List<Sample> list = scl.getValue().samples;

				if (scl.getValue().column < s.getColumn()) scl.getValue().indexStart = scl.getValue().indexEnd;

				boolean set = false;

				for (int sampleIndex = scl.getValue().indexStart; sampleIndex < list.size(); sampleIndex++) {
					Sample cs = list.get(sampleIndex);
					if (s.getColumn() == cs.getColumn() && Math.abs(s.getRow() - cs.getRow()) < 1) {
						set = true;
					}
					if (set || s.getColumn() < cs.getColumn()) {
						scl.getValue().indexEnd = Math.max(scl.getValue().indexEnd, sampleIndex);
						break;
					}
				}

				valid = valid && set;

				if (!valid) break;
			}
			if (!valid) {
				sampleList.remove(s);
			}
		}

		this.sampleCache.put(this.frameCacheCount, new SampleCacheContainer(copy));
		this.frameCacheCount = ++this.frameCacheCount % Configuration.getInstance().noiseFrameCache;

		for (int count = 0; count < Configuration.getInstance().noiseFrameCache; count++) {
			if (this.sampleCache.containsKey(count)) {
				this.sampleCache.get(count).indexStart = 0;
				this.sampleCache.get(count).indexEnd = 0;
			}
		}
	}

	private float getThreshold(float[] pixels, int index) {
		index = Math.min(Math.max(index, 2), pixels.length - 3);

		return (pixels[Math.max(0, index-2)]
		            + pixels[Math.max(0, index-1)]
				 	+ pixels[index]
					+ pixels[Math.min(index+1, pixels.length-1)]
					+ pixels[Math.min(index+2, pixels.length-1)]) / 5;
	}

	private ColumnScanResult scanColumn(float threshold, int column, Format frame, int lastRow) {
		int lightSum = 0;
		int lightMax = 0;
		int openCount = 0;
		float sampleRowSum = 0;
		int sampleLight = 0;

		List<Sample> samples = new ArrayList<Sample>();
		Sample sample = null;

		int rowMin = 0;
		int rowMax = frame.getHeight();

		if (!Configuration.getInstance().useTopLaser) rowMin = rowMax / 3 / 2 * 3;
		if (!Configuration.getInstance().useBottomLaser) rowMax = rowMax / 3 / 2 * 3;

		for (int row = rowMin; row < rowMax; row+=3) {
			int light = frame.getPixelRed(column, row);
			lightSum += light;
			lightMax = Math.max(lightMax, light);

			if (light > threshold) {
				openCount++;
				sampleRowSum += row / 3;
				sampleLight += light;
			} else if (openCount > 0 && sampleRowSum > 0) {
				float estrow = sampleRowSum / openCount;
				if (estrow > frame.getHeight() / 6) {
					estrow = frame.getHeight() / 3 - estrow;
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
				&& Math.min(sample.getRow(), frame.getHeight() - sample.getRow())
					> Math.min(samples.get(1).getRow(), frame.getHeight() - samples.get(1).getRow()))
		{
			sample = samples.get(1);
		}

		return new ColumnScanResult((lightSum / frame.getHeight() + lightMax) / 2, sample);
	}
}

class SampleCacheContainer {

	public List<Sample> samples;
	public int column;
	public int indexStart;
	public int indexEnd;

	public SampleCacheContainer(List<Sample> samples) {
		this.samples = samples;
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
