package org.unknown.marvin;
import java.util.List;

import log.LoggerServer;
import map.Map;
import map.MapUpdater;
import sample.SampleScanner;
import video.Video;
import video.VideoDeviceInfo;
import video.VideoException;
import au.edu.jcu.v4l4j.exceptions.V4L4JException;


public class Marvin {

	private LoggerServer logger = new LoggerServer();
	private Video video = new Video();

	/**
	 * @param args
	 * @throws V4L4JException
	 * @throws VideoException
	 * @throws InterruptedException
	 */
	public static void main(String[] args) {
		
		Marvin marvin = new Marvin();
		marvin.run();
		
	}

	private void run() {
		
		try {

			logger.setMarvin(this);
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
	
	public LoggerServer getLogger() {
		return logger;
	}
	
	public Video getVideo() {
		return video;
	}

}