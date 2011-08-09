package log;

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

}
