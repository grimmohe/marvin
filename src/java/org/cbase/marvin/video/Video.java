package org.cbase.marvin.video;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FilenameFilter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Properties;

import org.cbase.marvin.conf.CameraPropertyResolver;
import org.cbase.marvin.conf.Configuration;

import au.edu.jcu.v4l4j.CaptureCallback;
import au.edu.jcu.v4l4j.Control;
import au.edu.jcu.v4l4j.ControlList;
import au.edu.jcu.v4l4j.FrameGrabber;
import au.edu.jcu.v4l4j.ImageFormat;
import au.edu.jcu.v4l4j.V4L4JConstants;
import au.edu.jcu.v4l4j.VideoDevice;
import au.edu.jcu.v4l4j.FrameInterval.DiscreteInterval;
import au.edu.jcu.v4l4j.ResolutionInfo.DiscreteResolution;
import au.edu.jcu.v4l4j.exceptions.ControlException;
import au.edu.jcu.v4l4j.exceptions.V4L4JException;

public class Video {

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

		Collections.sort(resultList);

		return resultList;
	}

	public VideoDeviceInfo getDeviceInfo(String devfile) throws V4L4JException, VideoException {
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
		Configuration conf = Configuration.getInstance();

		for (ImageFormat imgf: vd.getDeviceInfo().getFormatList().getRGBEncodableFormats()) {
			for (DiscreteResolution res: imgf.getResolutionInfo().getDiscreteResolutions()) {
				for (DiscreteInterval interval: res.interval.getDiscreteIntervals()) {
					int frames = interval.denominator / Math.max(1, interval.numerator);

					if ( frames >= conf.videoFramesMin
					     && (opt == null
					         || (frames <= opt.interval
						         && res.height >= opt.height
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
				configureDevice();
			} catch (V4L4JException e) {
				e.printStackTrace();
				throw new VideoException("video device not avaiable. ", e);
			} catch (FileNotFoundException e) {
				throw new VideoException(e);
			} catch (IOException e) {
				throw new VideoException(e);
			}
		}
	}

	private void configureDevice()
			throws FileNotFoundException, IOException, V4L4JException {

		Properties properties = (new CameraPropertyResolver()).resolveProperties(
				activeVideo.getDeviceInfo().getName());

		if(properties != null) {
			for (Map.Entry<Object, Object> entry: properties.entrySet()) {
				Control control = activeVideo.getControlList().getControl((String) entry.getKey());
				System.out.println("set cam config: " + entry.getKey() + "=" +
						entry.getValue() + "(was: " + control.getValue() + ")");
				try {
					control.setValue(Integer.valueOf((String) entry.getValue()));
				} catch (ControlException e) {
					// pass
				}
			}
		}

	}

	public void saveDeviceConfiguration()
			throws FileNotFoundException, IOException, V4L4JException {

		CameraPropertyResolver propertyResolver =
			new CameraPropertyResolver();

		Properties properties = propertyResolver.resolveProperties(
				activeVideo.getDeviceInfo().getName());

		ControlList controlList = activeVideo.getControlList();

		for (Control control : controlList.getList()) {
			properties.setProperty(control.getName(),
					Integer.toString(control.getValue()));
		}

		propertyResolver.storeProperties(properties,
				activeVideo.getDeviceInfo().getName());

	}

	public void startStreaming(CaptureCallback cc) throws V4L4JException, VideoException {
		DeviceOptimals opt = getDeviceOptimals(activeVideo);

		if (activeFrameGrabber != null) {
			throw new VideoException("there is a stream running");
		}

		Configuration conf = Configuration.getInstance();
		conf.camRecession = conf.videoLaserDistance * Math.tan(Math.toRadians(90F - (conf.videoVAngle / 2))); // wie weit die cam hinter der Null-Distanz positioniert ist

		activeFrameGrabber = activeVideo.getRGBFrameGrabber(opt.width,
				opt.height, opt.input, opt.channel);
		activeFrameGrabber.setFrameInterval(opt.intervalNumerator,
				opt.intervalDenominator);
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
