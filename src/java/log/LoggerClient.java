package log;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import sample.RawImageData;
import sample.Sample;

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

		System.out.println(clientCb);
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


	private RawImageData deserializeRawImage(byte[] data)
			throws IOException, ClassNotFoundException {
		return (RawImageData) SerializationUtil.deserializeObject(data).readObject();
	}
	
	@SuppressWarnings("unchecked")
	private List<Sample> deserializeSampleList(byte[] data)
			throws IOException, ClassNotFoundException {
		return (ArrayList<Sample>) SerializationUtil.deserializeObject(data).readObject();
	}

}
