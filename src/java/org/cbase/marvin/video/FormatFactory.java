package org.cbase.marvin.video;

import au.edu.jcu.v4l4j.V4L4JConstants;

public class FormatFactory {

	protected static FormatFactory instance;

	protected FormatFactory() {

	}

	public static FormatFactory getInstance() {
		if (instance == null) {
			instance = new FormatFactory();
		}

		return instance;
	}

	public Format getFormat(int formatIndex) {

		Format format;

		switch (formatIndex) {
			case V4L4JConstants.IMF_YUYV:
				format = new FormatYUYV();
				break;
			default:
				throw new IllegalArgumentException("Format index " + formatIndex + "not supported.");
		}

		format.setFormat(formatIndex);

		return format;
	}

}
