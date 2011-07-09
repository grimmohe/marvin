package log;

import java.io.IOException;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.ArrayList;
import java.util.List;

import conf.Configuration;

public class ServerImpl extends Thread implements Server {
	private ServerSocket server;
	private List<Socket> clients = new ArrayList<Socket>();


	@Override
	public synchronized void start() {
		while ( this.server == null ) {
			try {
				this.server = new ServerSocket( Configuration.logginPort );
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
		for (Socket client: this.clients) {
			try {
				client.close();
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
		while ( !Thread.interrupted() ) {
			Socket client = null;
			try {
				client = server.accept();
				this.clients.add( client );
				System.out.println("client connected from " + client.getInetAddress());
			} catch ( IOException e ) {
				e.printStackTrace();
			}
	    }
	}

	/*
	 * send data to all connected clients
	 */
	public void write(int id, byte[] data) {
		Socket client = null;

		for (int clientIndex = 0; clientIndex < this.clients.size(); clientIndex++) {
			try {
				client = this.clients.get(clientIndex);

				if ( client.isConnected() ) {
					OutputStream out = client.getOutputStream();
					out.write(id);

					int len = data.length;
					for (int i = 3; i >= 0; i--) {
						out.write((len >> (i*8)) & 0x000000FF);
					}

					out.write(data);
				} else {
					disconnectClient(client);
				}

			} catch (IOException e) {
				disconnectClient(client);
				System.out.println(e.getMessage());
			}
		}
	}

	private void disconnectClient(Socket client) {
		if (client.isConnected()) {
			try {
				System.out.println("client disconnecting from " + client.getInetAddress());
				client.close();
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

}
