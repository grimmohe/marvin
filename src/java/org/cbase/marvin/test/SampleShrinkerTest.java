package org.cbase.marvin.test;


import static org.junit.Assert.*;

import java.util.ArrayList;
import java.util.List;

import org.cbase.marvin.sample.Sample;
import org.cbase.marvin.sample.SampleShrinker;
import org.junit.Test;



public class SampleShrinkerTest {

	@Test
	public void testSampleShrinker() {

		SampleShrinker sampleShrinker = new SampleShrinker();

		sampleShrinker.adapt(createSampleList());

		List<Sample> shrinkedSampleList = sampleShrinker.getSampleList();
		assertEquals(2, shrinkedSampleList.size());
		assertEquals(4L, shrinkedSampleList.get(0).getRow(), 0);
		assertEquals(0L, shrinkedSampleList.get(1).getRow(), 0);

	}

	private List<Sample> createSampleList() {

		List<Sample> sampleList = new ArrayList<Sample>();

		sampleList.add(new Sample(1, 0));
		sampleList.add(new Sample(1, 0));
		sampleList.add(new Sample(2, 0));
		sampleList.add(new Sample(2, 0));
		sampleList.add(new Sample(3, 0));
		sampleList.add(new Sample(3, 0));
		sampleList.add(new Sample(4, 0));
		sampleList.add(new Sample(4, 0));
		sampleList.add(new Sample(3, 0));
		sampleList.add(new Sample(3, 0));
		sampleList.add(new Sample(2, 0));
		sampleList.add(new Sample(2, 0));
		sampleList.add(new Sample(1, 0));
		sampleList.add(new Sample(1, 0));
		sampleList.add(new Sample(0, 0));
		sampleList.add(new Sample(0, 0));
		sampleList.add(new Sample(1, 0));
		sampleList.add(new Sample(1, 0));
		sampleList.add(new Sample(2, 0));
		sampleList.add(new Sample(2, 0));

		return sampleList;

	}

}
