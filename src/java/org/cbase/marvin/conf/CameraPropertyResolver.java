package org.cbase.marvin.conf;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Properties;

public class CameraPropertyResolver {

	private String propertiesPath = "camera-properties";
	
	public Properties resolveProperties(String cameraName) 
			throws FileNotFoundException, IOException {
		
		Properties properties = new Properties();
		
		File propertyFile = new File(propertiesPath, cameraName);
		if(propertyFile.exists()) {
			properties.load(new FileInputStream(propertyFile));
		}
		
		return properties;
		
	}
	
	public void storeProperties(Properties properties, String cameraName) 
			throws IOException {
		
		File propertyFile = new File(propertiesPath, cameraName);
		if(!propertyFile.exists()) {
			propertyFile.getParentFile().mkdirs();
			propertyFile.createNewFile();
		}
		properties.store(new FileOutputStream(propertyFile), 
				"Properties for camera " + cameraName);
		
	}
	
}
