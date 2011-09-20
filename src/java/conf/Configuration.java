package conf;


public class Configuration {

	public int videoFramesMin = 10;
	public int videoVAngle = 25; //42,91
	public int videoHAngle = 26;
	public int videoLaserDistance = 8;
	public int videoViewVAngle = 25;
	public int logginPort = 2889;
	public int noiseFrameCache = 3;

	public boolean useTopLaser = true;
	public boolean useBottomLaser = false;

	public String loggingServerAddress = "localhost";

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
