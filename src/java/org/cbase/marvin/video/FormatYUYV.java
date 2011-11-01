package org.cbase.marvin.video;

public class FormatYUYV implements Format {

	protected byte[] data;
	protected int height;
	protected int width;
	protected int formatid;

	@Override
	public int getPixelClear(int x, int y) {
		int position = (y * this.width + x) * 2;

		long Y = data[position] & 0xFF;
		long U = (data[position + 1 - ((position / 2 % 2) * 2)] & 0xFF) - 128;
		long V = (data[position + 1 + ((1 - (position / 2 % 2)) * 2)] & 0xFF) - 128;

		int R = (int)(Y + (1.370705 * V));
		int G = (int)(Y - (0.698001 * V) - (0.337633 * U));
		int B = (int)(Y + (1.732446 * U));

		if (R>255) R = 255;
		if (G>255) G = 255;
		if (B>255) B = 255;
		if (R<0) R = 0;
		if (G<0) G = 0;
		if (B<0) B = 0;

		return (int)((0xff << 24) | (R << 16) | (G << 8) | B);
	}

	@Override
	public int getPixelRed(int x, int y) {
		int position = (y * this.width + x) * 2;

		long Y = data[position] & 0xFF;
		long U = (data[position + 1 - ((position / 2 % 2) * 2)] & 0xFF) - 128;
		long V = (data[position + 1 + ((1 - (position / 2 % 2)) * 2)] & 0xFF) - 128;

		int R = (int)((Y + (1.370705 * V)) - (Y - (0.698001 * V) - (0.337633 * U) + (Y + (1.732446 * U))) / 2);

		if (R>255) R = 255;
		if (R<0) R = 0;

		return (int)(R << 16);
	}

	@Override
	public void setFrame(byte[] data, int width, int height) {

		this.data = data;
		this.height = height;
		this.width = width;

	}

	@Override
	public int getHeight() {
		return this.height;
	}

	@Override
	public int getWidth() {
		return this.width;
	}

	@Override
	public void setFormat(int formatid) {
		this.formatid = formatid;
	}

	@Override
	public int getFormat() {
		return this.formatid;
	}

	@Override
	public byte[] getBytes() {
		return this.data;
	}

}
