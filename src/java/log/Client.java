package log;

import java.io.IOException;
import java.io.InputStream;
import java.net.Socket;

import conf.Configuration;

public class Client extends Thread {

	private Logger logger;
	private Socket server;

	public Client(Logger logger) {
		super();
		this.logger = logger;
		this.start();
	}

	@Override
	public void run() {
		this.server = null;

		InputStream in;

		endless: while (true) {

			while ( this.server != null && this.server.isConnected() ) {
				try {
					in = this.server.getInputStream();
				} catch (IOException e) {
					e.printStackTrace();
					this.disconnect();
					continue endless;
				}

				/*
				 * data is expected in the following struct
				 * 1 byte to identify the following data
				 * 4 byte as integer to announce the length of the following data stream
				 * n byte as announced above with user data
				 */
				try {
					int id = in.read();
					int length = 0;

					for (int i = 3; i >= 0; i--) {
						length += (this.read(in) & 0x000000FF) << (i*8);
					}

					int read = 0;
					byte[] data = new byte[length];
					while ( read < length) {
						read += this.read(in, data, read, length - read);
					}

					if (this.logger != null) {
						logger.recreate(id, data);
					}
				} catch ( Exception e ) {
					System.out.println(e.getMessage());
					this.disconnect();
					continue endless;
				}
			}

			this.sleepStep();
		}
	}

	private int read(InputStream in) throws IOException {
		int value = in.read();

		if (value < 0) throw new IOException("End of stream");

		return value;
	}

	private int read(InputStream in, byte[] data, int offset, int length) throws IOException {
		int value = in.read(data, offset, length);

		if (value < 0) throw new IOException("End of stream");

		return value;
	}

	public void connect() {
		for (int tryCount = 0; tryCount < 60 && (this.server == null || !this.server.isConnected()); tryCount++) {
			try {
				this.server = new Socket(Configuration.loggingServerAddress, Configuration.logginPort);
				System.out.println("Connection established");
			} catch (IOException e) {
				System.out.println(e.getMessage());
				this.sleepStep();
			}
		}
	}

	public void disconnect() {
		if (this.server != null && this.server.isConnected()) {
			try {
				System.out.println("Connection closing");
				this.server.close();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}

		this.server = null;
	}

	private void sleepStep() {
		try {
			Thread.sleep(500);
		} catch (InterruptedException e) {
			e.printStackTrace();
		}
	}

}
