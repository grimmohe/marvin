package org.cbase.marvin.test;

import static org.junit.Assert.*;


import org.cbase.marvin.map.Position;
import org.cbase.marvin.sample.Sample;
import org.junit.Test;


public class SampleTest {

	@Test
	public void checkPosition1() {

		Sample sample = new Sample(0, 0);
		sample.setDistance(5);
		sample.setAngle(0);
		Position pos = sample.getPosition();
		assertTrue(pos.x == 0 && pos.y == 5);

	}

	@Test
	public void checkPosition2() {

		Sample sample = new Sample(0, 0);
		sample.setDistance(5);
		sample.setAngle(90);
		Position pos = sample.getPosition();
		assertTrue((int)(pos.x*100) == 500 && (int)(pos.y*100) == 0);

	}

	@Test
	public void checkPosition3() {

		Sample sample = new Sample(0, 0);
		sample.setDistance(5);
		sample.setAngle(-90);
		Position pos = sample.getPosition();
		assertTrue((int)(pos.x*100) == -500 && (int)(pos.y*100) == 0);

	}

	@Test
	public void checkPosition4() {

		Sample sample = new Sample(0, 0);
		sample.setDistance(5);
		sample.setAngle(-45);
		Position pos = sample.getPosition();
		assertTrue((int)(pos.x*100) == -353 && (int)(pos.y*100) == 353);

	}

}
