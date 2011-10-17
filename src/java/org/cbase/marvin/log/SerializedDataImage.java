package org.cbase.marvin.log;

import java.io.ByteArrayOutputStream;
import java.io.IOException;

import javax.imageio.ImageIO;

import au.edu.jcu.v4l4j.VideoFrame;

public class SerializedDataImage implements SerializedData {

	private VideoFrame frame;
	private byte[] data;

	public SerializedDataImage(VideoFrame frame) {
		super();
		this.frame = frame;
	}

	@Override
	public byte[] getData() {
		if (data == null) {
			try {
				ByteArrayOutputStream beos = new ByteArrayOutputStream();
				ImageIO.write(frame.getBufferedImage(), "jpg", beos);
				data = beos.toByteArray();
				beos.close();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
		return data;
	}

}
