package org.cbase.marvin.test;

import org.cbase.marvin.db.Database;
import org.junit.Test;


public class DatabaseTest {

	@Test
	public void createAndDelete() {
		Database.getInstance().shutdownDatabase();
	}

}
