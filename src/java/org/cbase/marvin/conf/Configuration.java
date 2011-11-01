package org.cbase.marvin.conf;


public class Configuration {

	public int videoFramesMin = 10;
	public int videoVAngle = 25; //42,91
	public int videoHAngle = 26;
	public int videoLaserDistance = 8;
	public int videoViewVAngle = 25;
	public int logginPort = 2889;
	public int noiseFrameCache = 3;
	public double camRecession  = 0;

	public boolean useTopLaser = true;
	public boolean useBottomLaser = false;

	public String loggingServerAddress = "192.168.0.100";

	private static Configuration configuration;

	public static Configuration getInstance() {
		if(configuration == null) {
			configuration =  new Configuration();
		}
		return configuration;
	}

	public static void SetConfigurationInstance(Configuration configuration) {
		Configuration.configuration = configuration;
	}

}
