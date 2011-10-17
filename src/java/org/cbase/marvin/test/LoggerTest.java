package org.cbase.marvin.test;

import static org.junit.Assert.assertTrue;

import java.io.ByteArrayInputStream;
import java.io.ObjectInputStream;
import java.util.ArrayList;
import java.util.List;

import org.cbase.marvin.log.LoggerServer;
import org.cbase.marvin.sample.Sample;
import org.junit.Test;



public class LoggerTest {

	@Test
	public void testLogSampleList() throws Exception {

		List<Sample> samples = new ArrayList<Sample>();
		samples.add(new Sample(2F, 1F));

		MocupServer server = new MocupServer();

		LoggerServer logger = new LoggerServer(server);

		logger.logSampleList(samples);

		ByteArrayInputStream bis = new ByteArrayInputStream(server.getResult());

		ObjectInputStream in = new ObjectInputStream(bis);

		List<Sample> samplesNew = (ArrayList<Sample>) in.readObject();

		assertTrue(samples.get(0).equals(samplesNew.get(0)));

	}

}
