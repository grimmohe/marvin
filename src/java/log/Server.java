package log;

import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.ArrayList;
import java.util.List;

import conf.Configuration;

public class Server extends Thread {

	private ServerSocket server;
	private List<Socket> clients = new ArrayList<Socket>();

	/*
	 * returns true, if any client is connected
	 */
	public boolean clientConnected () {
		return !this.clients.isEmpty();
	}

	@Override
	public synchronized void start() {
		while ( this.server == null ) {
			try {
				this.server = new ServerSocket( Configuration.logginPort );
			} catch ( IOException e ) {
				System.out.println(e.getMessage());
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
		while ( !this.interrupted() ) {
			Socket client = null;
			try {
				client = server.accept();
				this.clients.add( client );
			} catch ( IOException e ) {
				e.printStackTrace();
			}
	    }
	}

	/*
	 * send data to all connected clients
	 */
	public void write(byte[] data) {
		for (Socket client: this.clients) {
			try {
				client.getOutputStream().write(data);
			} catch (IOException e) {
				this.clients.remove(client);
				System.out.println(e.getMessage());
			}
		}
	}

}