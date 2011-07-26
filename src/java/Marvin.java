import log.Logger;
import map.Map;
import map.MapUpdater;
import sample.SampleScanner;
import video.Video;
import video.VideoDeviceInfo;
import video.VideoException;
import au.edu.jcu.v4l4j.exceptions.V4L4JException;


public class Marvin {

	/**
	 * @param args
	 * @throws V4L4JException
	 * @throws VideoException
	 * @throws InterruptedException
	 */
	public static void main(String[] args) throws VideoException, V4L4JException, InterruptedException {

		Logger logger = new Logger();
		Video video = new Video();

		VideoDeviceInfo vdi = video.getDeviceInfo("/dev/video2");
		System.out.println(vdi);
		video.setActiveVideoDevice(vdi);

		Map map = new Map();
		MapUpdater updater = new MapUpdater(map);

		SampleScanner ss = new SampleScanner(updater, logger);

		video.startStreaming(ss);

		while (true) {
			Thread.sleep(2000);
		}

	}

}