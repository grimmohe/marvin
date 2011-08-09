package log;

import static org.junit.Assert.assertEquals;

import org.junit.Test;


public class ClientTest {

	@Test
	public void testWiches() throws Exception {
		
		Client client = new Client(new LoggerClient(new NullClientLoggerCallback()));
		
		client.setWichesNodeList(true);
		client.setWichesRawImage(true);
		client.setWichesSampleList(true);
		
		assertEquals(true, client.whiches(LoggerCommon.NODE_LIST));
		assertEquals(true, client.whiches(LoggerCommon.RAW_IMAGE));
		assertEquals(true, client.whiches(LoggerCommon.SAMPLE_LIST));
		assertEquals(false, client.whiches(LoggerCommon.RECOGNIZED_ROWS));
		
	}
	
}
