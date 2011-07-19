package test;

import db.Database;
import org.junit.Test;


public class DatabaseTest {

	@Test
	public void createAndDelete() {
		Database.getInstance().shutdownDatabase();
	}

}
