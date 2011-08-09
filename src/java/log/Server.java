package log;


public interface Server {

	/*
	 * returns true, if any client is connected
	 */
	public boolean isClientConnected ();

	public void close();

	public void write(int id, SerializedData serializedData) ;

	public void start();

}