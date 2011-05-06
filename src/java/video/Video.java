package video;
import java.io.File;
import java.io.FilenameFilter;
import java.util.ArrayList;
import java.util.List;

import au.edu.jcu.v4l4j.CaptureCallback;
import au.edu.jcu.v4l4j.FrameGrabber;
import au.edu.jcu.v4l4j.ImageFormat;
import au.edu.jcu.v4l4j.V4L4JConstants;
import au.edu.jcu.v4l4j.VideoDevice;
import au.edu.jcu.v4l4j.FrameInterval.DiscreteInterval;
import au.edu.jcu.v4l4j.ResolutionInfo.DiscreteResolution;
import au.edu.jcu.v4l4j.exceptions.V4L4JException;
import conf.Configuration;

public class Video {

	private Configuration configuration;

	private VideoDevice activeVideo;
	private FrameGrabber activeFrameGrabber;

	private List<String> getDeviceFileList() {
		File dev = new File("/dev");

		FilenameFilter filter = new FilenameFilter() {
			public boolean accept(File dir, String name) {
				return name.startsWith("video");
			}
		};

		File[] fl = dev.listFiles(filter);
		List<String> resultList = new ArrayList<String>();

		for (File file : fl) {
			resultList.add(file.getAbsolutePath());
		}

		return resultList;
	}

	private VideoDeviceInfo getDeviceInfo(String devfile) throws V4L4JException, VideoException {
		VideoDeviceInfo vdi = null;

		VideoDevice vd = new VideoDevice(devfile);
		try {
			DeviceOptimals opt = getDeviceOptimals(vd);
			vdi = new VideoDeviceInfo(vd.getDeviceInfo().getName(), devfile, opt.toNiceString());
		} finally {
			vd.release();
		}

		return vdi;
	}

	private DeviceOptimals getDeviceOptimals(VideoDevice vd) throws V4L4JException, VideoException {
		DeviceOptimals opt = null;

		for (ImageFormat imgf: vd.getDeviceInfo().getFormatList().getNativeFormats()) {
			for (DiscreteResolution res: imgf.getResolutionInfo().getDiscreteResolutions()) {
				for (DiscreteInterval interval: res.interval.getDiscreteIntervals()) {
					int frames = interval.denominator / Math.max(1, interval.numerator);

					if ( frames >= configuration.videoFramesMin
					     && (opt == null
					         || (frames < opt.interval
						         && res.height > opt.height
						         && res.width >= opt.width) ) )
					{
						opt = new DeviceOptimals();
						opt.interval = frames;
						opt.intervalNumerator = interval.numerator;
						opt.intervalDenominator = interval.denominator;
						opt.height = res.height;
						opt.width = res.width;
					}
				}
			}
		}

		if ( opt == null ) {
			throw new VideoException("no suitable video format available");
		}

		return opt;
	}

	public Video(Configuration configuration) {
		this.configuration = configuration;
	}

	@Override
	protected void finalize() {
		try {
			setActiveVideoDevice(null);
		} catch (VideoException e) {
			e.printStackTrace();
		}
	}

	public List<VideoDeviceInfo> getVideoDevices() throws V4L4JException, VideoException {
		List<String> devicefiles = getDeviceFileList();
		List<VideoDeviceInfo> vdl = new ArrayList<VideoDeviceInfo>();

		for (String devfile: devicefiles) {
			vdl.add(getDeviceInfo(devfile));
		}

		return vdl;
	}

	public void setActiveVideoDevice(VideoDeviceInfo vd) throws VideoException {
		if (activeVideo != null) {
			stopStreaming();
			activeVideo.release();
		}

		if (vd != null) {
			try {
				activeVideo = new VideoDevice(vd.getDevice());
			} catch (V4L4JException e) {
				e.printStackTrace();
				throw new VideoException("video device not avaiable. " + e.getMessage());
			}
		}
	}

	public void startStreaming(CaptureCallback cc) throws V4L4JException, VideoException {
		DeviceOptimals opt = getDeviceOptimals(activeVideo);

		if (activeFrameGrabber != null) {
			throw new VideoException("there is a stream running");
		}

		activeFrameGrabber = activeVideo.getRGBFrameGrabber(opt.width, opt.height, opt.input, opt.channel);
		activeFrameGrabber.setCaptureCallback(cc);
		activeFrameGrabber.startCapture();
	}

	public void stopStreaming() {
		if (activeVideo != null && activeFrameGrabber != null) {
			activeVideo.releaseFrameGrabber();
			activeFrameGrabber = null;
		}
	}

}

class DeviceOptimals {
	public int height = 0;
	public int width = 0;
	public int intervalNumerator = 1;
	public int intervalDenominator = 1;
	public int interval = 0;
	public int input = 0;
	public int channel = V4L4JConstants.STANDARD_WEBCAM;

	public String toNiceString() {
		return " " + width + "x" + height + " " + intervalNumerator + "/" + intervalDenominator;
	}
}
