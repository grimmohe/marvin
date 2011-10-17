package org.cbase.marvin.test;


import org.cbase.marvin.video.Video;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;


import au.edu.jcu.v4l4j.CaptureCallback;
import au.edu.jcu.v4l4j.VideoFrame;
import au.edu.jcu.v4l4j.exceptions.V4L4JException;

public class VideoTest {

	@Before
	public void setUp() throws Exception {
	}

	@After
	public void tearDown() throws Exception {
	}

	@Test
	public void runstream() throws Exception {
		Capture cap = new Capture();
		Video video = new Video();

		video.setActiveVideoDevice(video.getVideoDevices().get(0));
		video.startStreaming(cap);

		Thread.sleep(10000);

		video.stopStreaming();

		float duration = (System.currentTimeMillis() - cap.firstframetime) / 1000;
		System.out.printf("Captured frames: %d in %f seconds (%f fps)\n", cap.framecounter, duration, cap.framecounter / duration);
	}
}

class Capture implements CaptureCallback {

	public int framecounter = 0;
	public long firstframetime = 0;

	public void exceptionReceived(V4L4JException arg0) {
		System.out.println(arg0.getMessage());
		arg0.printStackTrace();
	}

	public void nextFrame(VideoFrame arg0) {
		if (firstframetime == 0) firstframetime = System.currentTimeMillis();
		framecounter++;
		arg0.recycle();
	}

}
