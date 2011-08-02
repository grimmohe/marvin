package sample;

import java.io.Serializable;

public class RawImageData implements Serializable {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	private byte[] frame;
	private int width;
	private int height;

	public RawImageData(byte[] bufferedImage, int width, int height) {
		super();
		this.frame = bufferedImage;
		this.width = width;
		this.height = height;
	}
	
	public byte[] getFrame() {
		return frame;
	}
	
	public int getHeight() {
		return height;
	}
	
	public int getWidth() {
		return width;
	}
	
}
