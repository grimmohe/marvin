package log;


public class SerializedDataProxy implements SerializedData {

	private Object list;
	private byte[] data;
	
	
	public SerializedDataProxy(Object list) {
		this.list = list;
	}

	@Override
	public byte[] getData() {
		if(data == null) {
			data = SerializationUtil.serializeObject(list);
		}
		return data;
	}

}
