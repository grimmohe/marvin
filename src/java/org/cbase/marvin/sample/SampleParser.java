package org.cbase.marvin.sample;

import java.util.List;

import org.cbase.marvin.video.Format;

public interface SampleParser {

	public abstract List<Sample> generateSamples(Format frame);

}
