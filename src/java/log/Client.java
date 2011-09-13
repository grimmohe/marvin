package log;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Socket;

import conf.Configuration;

public class Client extends Thread {

	private LoggerClient logger;
	private Socket serverSocket;
	private Socket mySocket;
	private boolean wichesRawImage=false;
	private boolean wichesSampleList=false;
	private boolean wichesNodeList=false;
	
	/* this id's must not overlay into logger id's */
	static final int CMD_WISHES_OFFSET = 100;
	private static final int CMD_WISHES_RAWIMAGE = CMD_WISHES_OFFSET + LoggerCommon.RAW_IMAGE;
	private static final int CMD_WISHES_SAMPLE_LIST = CMD_WISHES_OFFSET + LoggerCommon.SAMPLE_LIST;
	private static final int CMD_WISHES_NODE_LIST = CMD_WISHES_OFFSET + LoggerCommon.NODE_LIST;

	static final int CMD_ACTION = 200;
	private static final int CMD_ACTION_SAVE_CAM_DATA = 201;
	
	public Client(LoggerClient logger) {
		this.logger = logger;
		this.start();
	}

	public Client(Socket clientSocket) {
		this.mySocket = clientSocket;
		this.start();
	}
	
	@Override
	public void run() {
		this.serverSocket = null;

		InputStream in;

		endless: while (true) {

			while ( this.serverSocket != null && this.serverSocket.isConnected() ) {
				try {
					in = this.serverSocket.getInputStream();
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

					if(id > CMD_WISHES_OFFSET) {
						switchWishes(id, data);
					} else {
						if (this.logger != null) {
							logger.recreate(id, data);
						}
					}
					
				} catch ( Exception e ) {
					e.printStackTrace();
					this.disconnect();
					continue endless;
				}
			}

			this.sleepStep();
		}
	}

	void switchWishes(int id, byte[] data) throws IOException, ClassNotFoundException {
		
		switch(id) {
			case CMD_WISHES_RAWIMAGE: {
				wichesRawImage = (Boolean) SerializationUtil.deserializeObject(data).readObject();
			}
			case CMD_WISHES_SAMPLE_LIST: {
				wichesSampleList = (Boolean) SerializationUtil.deserializeObject(data).readObject();
			}
			case CMD_WISHES_NODE_LIST: {
				wichesNodeList = (Boolean) SerializationUtil.deserializeObject(data).readObject();
			}
		}
		
	}

	private int read(InputStream in) throws IOException {
		int value = in.read();

		if (value < 0) throw new IOException("End of stream");

		return value;
	}

	private int read(InputStream in, byte[] data, int offset, int length) 
			throws IOException {
		int value = in.read(data, offset, length);

		if (value < 0) throw new IOException("End of stream");

		return value;
	}

	public void connect() {
		for (int tryCount = 0; tryCount < 60 && (this.serverSocket == null || 
				!this.serverSocket.isConnected()); tryCount++) {
			try {
				this.serverSocket = new Socket(Configuration.loggingServerAddress, 
						Configuration.logginPort);
				System.out.println("Connection established");
			} catch (IOException e) {
				System.out.println(e.getMessage());
				this.sleepStep();
			}
		}
	}

	public void disconnect() {
		if (this.serverSocket != null && this.serverSocket.isConnected()) {
			try {
				System.out.println("Connection closing");
				this.serverSocket.close();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}

		this.serverSocket = null;
	}

	private void sleepStep() {
		try {
			Thread.sleep(500);
		} catch (InterruptedException e) {
			e.printStackTrace();
		}
	}

	public boolean whiches(int id) {
		switch (id + CMD_WISHES_OFFSET) {
			case CMD_WISHES_NODE_LIST: return wichesNodeList;
			case CMD_WISHES_RAWIMAGE: return wichesRawImage;
			case CMD_WISHES_SAMPLE_LIST: return wichesSampleList;
		}
		return false;
	}
	
	public void setWichesRawImage(boolean whichesRawImage) throws IOException {
		this.wichesRawImage = whichesRawImage;
		sendWhichesToServer(CMD_WISHES_RAWIMAGE, this.wichesRawImage);
	}

	public void setWichesSampleList(boolean whichesSampleList) throws IOException {
		this.wichesSampleList = whichesSampleList;
		sendWhichesToServer(CMD_WISHES_SAMPLE_LIST, this.wichesSampleList);
	}

	public void setWichesNodeList(boolean whichesNodeList) throws IOException {
		this.wichesNodeList = whichesNodeList;
		sendWhichesToServer(CMD_WISHES_NODE_LIST, this.wichesNodeList);
	}

	public void camSaveCommand() throws IOException {
		sendWhichesToServer(CMD_ACTION_SAVE_CAM_DATA, false);
	}
	
	private void sendWhichesToServer(int cmdId,
			boolean flag) throws IOException {
		
		write(cmdId, SerializationUtil.serializeObject(flag));
		
	}
	
	/*
	 * send data to all connected clients
	 */
	public synchronized void write(int id, byte[] data) throws IOException {

		if(serverSocket != null) {
			if ( serverSocket.isConnected() ) {
				OutputStream out = serverSocket.getOutputStream();
				out.write(id);
				int len = data.length;
				for (int i = 3; i >= 0; i--) {
					out.write((len >> (i*8)) & 0x000000FF);
				}
	
				out.write(data);
			} else {
				disconnect();
			}
		}
	}	

	public Socket getMySocket() {
		return mySocket;
	}

	@Override
	public String toString() {
		return "Client [mySocket=" + mySocket + ", serverSocket="
				+ serverSocket + ", wichesNodeList=" + wichesNodeList
				+ ", wichesRawImage=" + wichesRawImage + ", wichesSampleList="
				+ wichesSampleList + "]";
	}
	
}
