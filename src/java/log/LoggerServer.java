package log;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;
import java.util.List;

import sample.RawImageData;
import sample.Sample;

/*
 * Write classes into a byte[] to send to listening clients and recreates them to be visualized in a gui.
 */
public class LoggerServer {

	private Server server;

	
	private static LoggerServer loggerInstance;

	public LoggerServer() {
		Server server = new ServerImpl();
		server.start();
		this.server = server;
	}

	public LoggerServer(Server server) {
		super();
		this.server = server;
	}

	public static LoggerServer getInstance() {
		if(loggerInstance == null) {
			loggerInstance = new LoggerServer();
		}
		return loggerInstance;
	}
	
	public void close() {
		if (this.server != null) {
			this.server.close();
		}
	}

	public void logRawImage(RawImageData imageData) {
		server.write(LoggerCommon.RAW_IMAGE, new SerializedDataProxy(imageData));
	}
	
	public void logRecognizedRows(List<Sample> rows) {
		server.write(LoggerCommon.RECOGNIZED_ROWS, new SerializedDataProxy(rows));
	}
	
	public void logNodeList(List<Sample> nodes) {
		server.write(LoggerCommon.NODE_LIST, new SerializedDataProxy(nodes));
	}

	public void logSampleList(List<Sample> samples) {
		server.write(LoggerCommon.SAMPLE_LIST, new SerializedDataProxy(samples));
	}

}