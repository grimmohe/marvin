package org.cbase.marvin.log;

import org.cbase.marvin.Marvin;

public interface Server {

	/*
	 * returns true, if any client is connected
	 */
	public boolean isClientConnected ();

	public void close();

	public void write(int id, SerializedData serializedData) ;

	public void start();

	public void setMarvin(Marvin marvin);
	
	public Marvin getMarvin();
	
}