package org.cbase.marvin.test;

import org.cbase.marvin.Marvin;
import org.cbase.marvin.log.SerializedData;
import org.cbase.marvin.log.Server;

public class MocupServer implements Server {

	private byte[] result;

	@Override
	public void close() {
		// TODO Auto-generated method stub

	}

	@Override
	public boolean isClientConnected() {
		return true;
	}

	@Override
	public void start() {
	}

	@Override
	public void write(int id, SerializedData data) {

		result = data.getData();
	}

	public byte[] getResult() {
		return result;
	}

	@Override
	public Marvin getMarvin() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void setMarvin(Marvin marvin) {
		// TODO Auto-generated method stub
		
	}

}
