package log;


public interface Server {

	/*
	 * returns true, if any client is connected
	 */
	public boolean isClientConnected ();

	public void close();

	public void write(int id, byte[] data) ;

	public void start();

}