package org.cbase.marvin.log;

import java.util.List;

import org.cbase.marvin.Marvin;
import org.cbase.marvin.sample.Sample;

import au.edu.jcu.v4l4j.VideoFrame;

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

	public void logRawImage(VideoFrame frame) {
		server.write(LoggerCommon.RAW_IMAGE, new SerializedDataImage(frame));
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

	public void setMarvin(Marvin marvin) {
		server.setMarvin(marvin);
	}

	public Marvin getMarvin() {
		return server.getMarvin();
	}

}