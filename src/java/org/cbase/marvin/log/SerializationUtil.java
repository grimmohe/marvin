package org.cbase.marvin.log;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;

public class SerializationUtil {
	
	public static byte[] serializeObject(Object o) {
		ByteArrayOutputStream bout = new ByteArrayOutputStream();
		ObjectOutputStream oout;
		try {
			oout = new ObjectOutputStream(bout);
			oout.writeObject(o);
			oout.close();
			bout.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
		return bout.toByteArray();
	}
	
	public static ObjectInputStream deserializeObject(byte[] data) throws IOException {
		ByteArrayInputStream bis = new ByteArrayInputStream(data);

		ObjectInputStream in = new ObjectInputStream(bis);		
		
		return in;
	}


}
