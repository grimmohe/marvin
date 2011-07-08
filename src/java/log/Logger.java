package log;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;
import java.util.List;

import sample.Sample;

/*
 * Write classes into a byte[] to send to listening clients and recreates them to be visualized in a gui.
 */
public class Logger {

	private Server server;
	private ClientLoggerCallback clientCb;

	private final static int SAMPLE_LIST = 1;

	public Logger() {
		super();
		Server server = new ServerImpl();
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
		ByteArrayOutputStream bout = new ByteArrayOutputStream();
		ObjectOutputStream oout;
		try {
			oout = new ObjectOutputStream(bout);
			oout.writeObject(samples);
		} catch (IOException e) {
			e.printStackTrace();
		}
		server.write(SAMPLE_LIST, bout.toByteArray());
	}

	/*
	 * called by log.Client()
	 * calls ClientLoggerCallback with deserialised data structs
	 */
	public void recreate(int ident, byte[] data)
			throws IOException, ClassNotFoundException {

		switch(ident) {
			case SAMPLE_LIST: {
				clientCb.newSampleList(deserializeSampleList(data));
			}
		}

	}

	private List<Sample> deserializeSampleList(byte[] data)
			throws IOException, ClassNotFoundException {

		ByteArrayInputStream bis = new ByteArrayInputStream(data);

		ObjectInputStream in = new ObjectInputStream(bis);

		return (ArrayList<Sample>) in.readObject();

	}

}