package org.cbase.marvin.log;

public class SerializedDataSimple implements SerializedData {

	private byte[] data;
	
	public SerializedDataSimple(byte[] data) {
		super();
		this.data = data;
	}

	@Override
	public byte[] getData() {
		return data;
	}

}
