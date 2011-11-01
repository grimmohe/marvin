package org.cbase.marvin.log;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.cbase.marvin.sample.Sample;
import org.cbase.marvin.video.Format;
import org.cbase.marvin.video.FormatFactory;


public class LoggerClient {

	private ClientLoggerCallback clientCb = new NullClientLoggerCallback();

	public LoggerClient(ClientLoggerCallback clientCb) {
		if(clientCb == null) {
			throw new IllegalArgumentException("ClientLoggerCallback could not be null");
		}
		this.clientCb = clientCb;
	}

	/*
	 * called by log.Client()
	 * calls ClientLoggerCallback with deserialised data structs
	 */
	public void recreate(int ident, byte[] data)
			throws IOException, ClassNotFoundException {

		switch(ident) {
			case LoggerCommon.NODE_LIST: {
				clientCb.newNodeList(deserializeSampleList(data));
				break;
			}
			case LoggerCommon.SAMPLE_LIST: {
				clientCb.newSampleList(deserializeSampleList(data));
				break;
			}
			case LoggerCommon.RAW_IMAGE: {
				clientCb.newRawImage(deserializeRawImage(data));
				break;
			}
			case LoggerCommon.RECOGNIZED_ROWS: {
				clientCb.newRowNodes(deserializeSampleList(data));
				break;
			}
		}

	}

	private Format deserializeRawImage(byte[] data)
			throws IOException, ClassNotFoundException {
		int imgFormat = toInt(data, 0);
		int width = toInt(data, 4);
		int height = toInt(data, 8);

		Format format = FormatFactory.getInstance().getFormat(imgFormat);
		format.setFrame(Arrays.copyOfRange(data, 12, data.length), width, height);

		return format;
	}

	private int toInt(byte[] data, int start) {
		int i = 0;

		i = (data[start] & 0xff) << 24;
		i |= (data[start + 1] & 0xff) << 16;
		i |= (data[start + 2] & 0xff) << 8;
		i |= data[start + 3] & 0xff;

		return i;
	}

	@SuppressWarnings("unchecked")
	private List<Sample> deserializeSampleList(byte[] data)
			throws IOException, ClassNotFoundException {
		return (ArrayList<Sample>) SerializationUtil.deserializeObject(data).readObject();
	}

}
