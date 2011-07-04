package log;

import java.util.List;

import sample.Sample;

/*
 * Write classes into a byte[] to send to listening clients and recreates them to be visualized in a gui.
 */
public class Logger {

	private Server server;
	private ClientLoggerCallback clientCb;

	public Logger() {
		super();
		Server server = new Server();
		server.start();
		this.server = server;
	}

	public Logger(ClientLoggerCallback clientCb) {
		super();
		this.clientCb = clientCb;
	}

	public Logger(Server server) {
		super();
		this.server = server;
	}

	public void close() {
		if (this.server != null) {
			this.server.close();
		}
	}

	public void logSampleList(List<Sample> samples) {

	}

	/*
	 * called by log.Client()
	 * calls ClientLoggerCallback with deserialised data structs
	 */
	public void recreate(int ident, byte[] data) {

	}

}