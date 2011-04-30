package video;

public class VideoDeviceInfo {

	private String name;
	private String device;
	private String optimals;

	public String getName() {
		return name;
	}
	public String getDevice() {
		return device;
	}
	public String getOptimals() {
		return optimals;
	}

	public VideoDeviceInfo(String name, String device, String optimals) {
		super();

		this.name = name;
		this.device = device;
		this.optimals = optimals;
	}

}
