package sample;

import java.util.List;

import au.edu.jcu.v4l4j.VideoFrame;

public interface SampleParser {

	public abstract List<Sample> generateSamples(VideoFrame frame);

}