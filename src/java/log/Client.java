package log;

import java.io.IOException;
import java.io.InputStream;
import java.net.Socket;

import conf.Configuration;

public class Client extends Thread {

	private Logger logger;

	public Client(Logger logger) {
		super();
		this.logger = logger;
	}

	@Override
	public void run() {
		Socket server = null;
		while ( server == null ) {
			try {
				server = new Socket(Configuration.loggingServerAddress, Configuration.logginPort);
			} catch (IOException e) {
				System.out.println(e.getMessage());
			}
		}

		InputStream in;
		try {
			in = server.getInputStream();
		} catch (IOException e) {
			e.printStackTrace();
			System.out.println("Logger connection closing");
			try {
				server.close();
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			return;
		}

		/*
		 * data is expected in the following struct
		 * 1 byte to identify the following data
		 * 4 byte as integer to announce the length of the following data stream
		 * n byte as announced above with user data
		 */
		while ( server.isConnected() ) {
			try {
				int id = in.read();
				int length = 0;

				for (int i = 3; i >= 0; i--) {
					length += (in.read() & 0x000000FF) << (i*8);
				}

				int read = 0;
				byte[] data = new byte[length];
				while ( read < length) {
					read += in.read(data, read, length - read);
				}

				logger.recreate(id, data);

			} catch ( IOException e ) {
				e.printStackTrace();
				System.out.println("Logger connection closing");
				try {
					server.close();
				} catch (IOException e1) {
					e1.printStackTrace();
				}
				return;
			}

		}
	}

}
