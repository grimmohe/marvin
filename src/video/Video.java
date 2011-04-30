package video;
import java.io.File;
import java.io.FilenameFilter;
import java.util.ArrayList;
import java.util.List;

import com.sun.xml.internal.fastinfoset.util.StringArray;

import conf.Configuration;

import au.edu.jcu.v4l4j.CaptureCallback;
import au.edu.jcu.v4l4j.Control;
import au.edu.jcu.v4l4j.FrameGrabber;
import au.edu.jcu.v4l4j.ImageFormat;
import au.edu.jcu.v4l4j.V4L4JConstants;
import au.edu.jcu.v4l4j.VideoDevice;
import au.edu.jcu.v4l4j.FrameInterval.DiscreteInterval;
import au.edu.jcu.v4l4j.ResolutionInfo.DiscreteResolution;
import au.edu.jcu.v4l4j.exceptions.V4L4JException;

public class Video {

	private Configuration configuration;

	private VideoDevice activeVideo = null;
	private FrameGrabber activeFrameGrabber = null;

	private String[] getDeviceFileList() {
		File dev = new File("/dev");

		FilenameFilter filter = new FilenameFilter() {
			public boolean accept(File dir, String name) {
				return name.startsWith("video");
			}
		};

		File[] fl = dev.listFiles(filter);
		String[] ret = new String[fl.length];

		for (int i=0; i<fl.length; i++) {
			ret[i] = (fl[i].getAbsolutePath());
		}

		return ret;
	}

	private VideoDeviceInfo getDeviceInfo(String devfile) throws Exception {
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

	private DeviceOptimals getDeviceOptimals(VideoDevice vd) throws Exception {
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
			throw new Exception("no compatible video format");
		}

		return opt;
	}

	public Video(Configuration configuration) {
		super();
		this.configuration = configuration;
	}

	protected void finalize() throws Throwable {
		setActiveVideoDevice(null);
	}

	public List<VideoDeviceInfo> getVideoDevices() {
		String[] devicefiles = this.getDeviceFileList();
		List<VideoDeviceInfo> vdl = new ArrayList<VideoDeviceInfo>();

		for (String devfile: devicefiles) {
			try {
				vdl.add(getDeviceInfo(devfile));
			} catch (V4L4JException e) {
				System.out.println("error reading device " + devfile);
				e.printStackTrace();
			} catch (Exception e) {
				System.out.println("error: " + e.getMessage());
				e.printStackTrace();
			}
		}

		return vdl;
	}

	public void setActiveVideoDevice(VideoDeviceInfo vd) throws Exception {
		if (activeVideo != null) {
			stopStreaming();
			activeVideo.release();
		}

		if (vd != null) {
			try {
				activeVideo = new VideoDevice(vd.getDevice());
			} catch (V4L4JException e) {
				e.printStackTrace();
				throw new Exception("video device not avaiable. " + e.getMessage());
			}
		}
	}

	public void startStreaming(CaptureCallback cc) throws Exception {
		DeviceOptimals opt = getDeviceOptimals(activeVideo);

		if (activeFrameGrabber != null) {
			throw new Exception("there is a stream running");
		}

		activeFrameGrabber = activeVideo.getRawFrameGrabber(opt.width, opt.height, opt.input, opt.channel);
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
