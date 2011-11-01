package org.cbase.marvin.log;

import java.io.ByteArrayOutputStream;
import java.io.IOException;

import org.cbase.marvin.video.Format;

public class SerializedDataImage implements SerializedData {

	private Format frame;
	private byte[] data;

	public SerializedDataImage(Format frame) {
		super();
		this.frame = frame;
	}

	@Override
	public byte[] getData() {
		if (data == null) {
			try {
				ByteArrayOutputStream baos = new ByteArrayOutputStream();

				baos.write(toByteArray(frame.getFormat()));
				baos.write(toByteArray(frame.getWidth()));
				baos.write(toByteArray(frame.getHeight()));
				baos.write(frame.getBytes());

				data = baos.toByteArray();
				baos.close();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
		return data;
	}

	private byte[] toByteArray(int i) {
		byte[] data = new byte[4];

		data[0] = (byte)((i >> 24) & 0xff);
		data[1] = (byte)((i >> 16) & 0xff);
		data[2] = (byte)((i >> 8) & 0xff);
		data[3] = (byte)(i & 0xff);

		return data;
	}

}
