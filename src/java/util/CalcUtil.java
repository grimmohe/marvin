package util;

public class CalcUtil {


	public static int getRed(int r, int g, int b) {
		return Math.max(0, r - (g + b) / 2);
	}

}
