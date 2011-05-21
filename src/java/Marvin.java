import map.Map;
import map.MapUpdater;
import sample.SampleScanner;
import video.Video;
import video.VideoException;
import au.edu.jcu.v4l4j.exceptions.V4L4JException;
import conf.Configuration;


public class Marvin {

	/**
	 * @param args
	 * @throws V4L4JException
	 * @throws VideoException
	 */
	public static void main(String[] args) throws VideoException, V4L4JException {

		Configuration configuration = new Configuration();
		Video video = new Video(configuration);

		video.setActiveVideoDevice(video.getVideoDevices().get(0));

		Map map = new Map();
		MapUpdater updater = new MapUpdater(map);

		SampleScanner ss = new SampleScanner(updater);

		video.startStreaming(ss);

	}

}