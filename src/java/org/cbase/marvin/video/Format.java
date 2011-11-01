package org.cbase.marvin.video;

public interface Format {

	public byte[] getBytes();

	public int getHeight();

	public int getWidth();

	public int getFormat();

	public int getPixelClear(int x, int y);

	public int getPixelRed(int x, int y);

	public void setFrame(byte[] data, int width, int height);

	public void setFormat(int formatid);

}
