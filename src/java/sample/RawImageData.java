package sample;

import java.io.Serializable;

import au.edu.jcu.v4l4j.VideoFrame;

public class RawImageData implements Serializable {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	VideoFrame frame;

	public RawImageData(VideoFrame frame) {
		super();
		this.frame = frame;
	}
	
	public VideoFrame getFrame() {
		return frame;
	}
	
}
