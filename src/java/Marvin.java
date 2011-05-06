import java.util.List;

import sample.Sample;
import sample.SampleScanner;
import sample.SampleUpdate;
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

		SampleScanner ss = new SampleScanner(new SampleUpdate() {

			public void update(List<Sample> sampleList) {
//				System.out.println("sampleupdate with " + sampleList.size() + " samples");

			}
		});

		video.startStreaming(ss);

	}

}