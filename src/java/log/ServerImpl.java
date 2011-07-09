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
			} catch ( IOException e ) {
				e.printStackTrace();
			}
	    }
	}

	/*
	 * send data to all connected clients
	 */
	public void write(int id, byte[] data) {
		for (Socket client: this.clients) {
			try {
				OutputStream out = client.getOutputStream();
				out.write(id);

				int len = data.length;
				for (int i = 3; i >= 0; i--) {
					out.write((len >> (i*8)) & 0x000000FF);
				}

				client.getOutputStream().write(data);
			} catch (IOException e) {
				this.clients.remove(client);
				System.out.println(e.getMessage());
			}
		}
	}

	@Override
	public boolean isClientConnected() {
		return !this.clients.isEmpty();
	}

}
