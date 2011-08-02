package log;

import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;
import java.util.List;

import javax.imageio.ImageIO;

import sample.Sample;

/*
 * Write classes into a byte[] to send to listening clients and recreates them to be visualized in a gui.
 */
public class Logger {

	private Server server;
	private ClientLoggerCallback clientCb = new NullClientLoggerCallback();

	private final static int RAW_IMAGE = 1;
	private final static int RECOGNIZED_ROWS = 2;
	private final static int SAMPLE_LIST = 3;
	private final static int NODE_LIST = 4;

	private static Logger loggerInstance;

	public Logger() {
		Server server = new ServerImpl();
		server.start();
		this.server = server;
	}

	public Logger(ClientLoggerCallback clientCb) {
		this.clientCb = clientCb;
	}

	public Logger(Server server) {
		super();
		this.server = server;
	}

	public static Logger getInstance() {
		if(loggerInstance == null) {
			loggerInstance = new Logger();
		}
		return loggerInstance;
	}

	public void close() {
		if (this.server != null) {
			this.server.close();
		}
	}

	public void logRawImage(byte[] imageData) {
		server.write(RAW_IMAGE, imageData);
	}

	public void logRecognizedRows(List<Sample> rows) {
		server.write(RECOGNIZED_ROWS, serializeObject(rows));
	}

	public void logNodeList(List<Sample> nodes) {
		server.write(NODE_LIST, serializeObject(nodes));
	}

	public void logSampleList(List<Sample> samples) {
		server.write(SAMPLE_LIST, serializeObject(samples));
	}

	private byte[] serializeObject(Object o) {
		ByteArrayOutputStream bout = new ByteArrayOutputStream();
		ObjectOutputStream oout;
		try {
			oout = new ObjectOutputStream(bout);
			oout.writeObject(o);
			oout.close();
			bout.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
		return bout.toByteArray();
	}

	/*
	 * called by log.Client()
	 * calls ClientLoggerCallback with deserialised data structs
	 */
	public void recreate(int ident, byte[] data)
			throws IOException, ClassNotFoundException {

		switch(ident) {
			case NODE_LIST: {
				clientCb.newNodeList(deserializeSampleList(data));
				break;
			}
			case SAMPLE_LIST: {
				clientCb.newSampleList(deserializeSampleList(data));
				break;
			}
			case RAW_IMAGE: {
				clientCb.newRawImage(deserializeRawImage(data));
				break;
			}
			case RECOGNIZED_ROWS: {
				clientCb.newRowNodes(deserializeSampleList(data));
				break;
			}
		}

	}

	private BufferedImage deserializeRawImage(byte[] data)
			throws IOException, ClassNotFoundException {
		ByteArrayInputStream bais = new ByteArrayInputStream(data);
		BufferedImage img = ImageIO.read(bais);
		bais.close();
		return img;
	}

	@SuppressWarnings("unchecked")
	private List<Sample> deserializeSampleList(byte[] data)
			throws IOException, ClassNotFoundException {
		return (ArrayList<Sample>) deserializeObject(data).readObject();
	}

	private ObjectInputStream deserializeObject(byte[] data) throws IOException {
		ByteArrayInputStream bis = new ByteArrayInputStream(data);

		ObjectInputStream in = new ObjectInputStream(bis);

		return in;
	}

}