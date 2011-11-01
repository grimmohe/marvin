package org.cbase.marvin.log;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketException;
import java.net.SocketTimeoutException;
import java.util.ArrayList;
import java.util.List;

import org.cbase.marvin.Marvin;
import org.cbase.marvin.conf.Configuration;


public class ServerImpl extends Thread implements Server {

	private ServerSocket server;
	private List<Client> clients = new ArrayList<Client>();
	protected Marvin marvin;

	@Override
	public synchronized void start() {
		while ( this.server == null ) {
			try {
				this.server = new ServerSocket( Configuration.getInstance().logginPort );
			} catch ( IOException e ) {
				System.out.println(e.getMessage());
				try {
					Thread.sleep(1000);
				} catch (InterruptedException e1) {
					e1.printStackTrace();
				}
			}
		}

		super.start();
	}

	public void close() {
		for (Client client: this.clients) {
			try {
				client.getMySocket().close();
			} catch (IOException e) {
				System.out.println(e.getMessage());
			}
		}

		try {
			this.server.close();
		} catch (IOException e) {
			System.out.println(e.getMessage());
		}

		this.interrupt();
	}

	@Override
	public void run() {
		try {
			server.setSoTimeout(50);
		} catch (SocketException e1) {
			e1.printStackTrace();
		}
		while ( !Thread.interrupted() ) {
			Socket client = null;
			try {
				client = server.accept();
				if(client != null) {
					this.clients.add( new Client( client ));
					System.out.println("client connected from " + client.getInetAddress());
				}
			} catch (SocketTimeoutException ex) {
				// pass
			} catch ( IOException e ) {
				e.printStackTrace();
			}
			readCmdsFromClients();
	    }
	}

	private void readCmdsFromClients() {
		for (Client client : clients) {
//			System.out.println("readCmds for client: " + client);
			readCmdFromClient(client);
		}
	}

	private void readCmdFromClient(Client client) {

		Socket clientSocket = client.getMySocket();

		if ( clientSocket != null && clientSocket.isConnected() ) {
			InputStream in = null;
			try {
				in = clientSocket.getInputStream();
			} catch (IOException e) {
				e.printStackTrace();
			}

			/*
			 * data is expected in the following struct
			 * 1 byte to identify the following data
			 * 4 byte as integer to announce the length of the following data stream
			 * n byte as announced above with user data
			 */
			try {
				if (in.available() <= 0) {
					return;
				}

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

				if(id > Client.CMD_WISHES_OFFSET) {
					client.switchWishes(id, data);
				}

				if(id > Client.CMD_ACTION) {
					marvin.getVideo().saveDeviceConfiguration();
				}
			} catch ( SocketException se ) {
				if (se.getMessage() != "Socket is closed") se.printStackTrace();
			} catch ( Exception e ) {
				e.printStackTrace();
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

	/*
	 * send data to all connected clients
	 */
	public synchronized void write(int id, SerializedData serializedData) {
		Socket clientSocket = null;
		Client client = null;


		for (int clientIndex = 0; clientIndex < this.clients.size(); clientIndex++) {
			try {
				client = this.clients.get(clientIndex);
				clientSocket = client.getMySocket();

				if ( clientSocket.isConnected()) {
					if(client.whiches(id)) {
//						System.out.println("write data for id: " + id );
						byte[] data = serializedData.getData();
						OutputStream out = clientSocket.getOutputStream();
						out.write(id);
						int len = data.length;
						for (int i = 3; i >= 0; i--) {
							out.write((len >> (i*8)) & 0x000000FF);
						}

						out.write(data);
					}
				} else {
					disconnectClient(client);
				}

			} catch (IOException e) {
				disconnectClient(client);
				System.out.println(e.getMessage());
			}
		}
	}

	private void disconnectClient(Client client) {
		Socket clientSocket = client.getMySocket();
		if (clientSocket.isConnected()) {
			try {
				System.out.println("client disconnecting from " + clientSocket.getInetAddress());
				clientSocket.close();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
		this.clients.remove(client);
	}

	@Override
	public boolean isClientConnected() {
		return !this.clients.isEmpty();
	}

	@Override
	public Marvin getMarvin() {
		return marvin;
	}

	@Override
	public void setMarvin(Marvin marvin) {
		this.marvin = marvin;
	}

}
