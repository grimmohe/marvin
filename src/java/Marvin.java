import java.util.List;

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
	public static void main(String[] args) {

		Logger logger = new Logger();
		Video video = new Video();

		try {
			List<VideoDeviceInfo> vdil = video.getVideoDevices();
			System.out.println(vdil.get(vdil.size()-1));
			video.setActiveVideoDevice(vdil.get(vdil.size()-1));

			Map map = new Map();
			MapUpdater updater = new MapUpdater(map);

			SampleScanner ss = new SampleScanner(updater, logger);

			video.startStreaming(ss);

			while (true) {
				Thread.sleep(2000);
			}
		} catch (Exception e) {
			e.printStackTrace();
		}

		video.stopStreaming();
		logger.close();
	}

}