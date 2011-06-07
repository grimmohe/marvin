package sample;

import map.Position;

public class Sample implements Comparable<Sample> {

	private float row;
	private int column;

	private float distance;
	private float angle;
	private float intensity;

	public Sample(float row, float intensity) {
		super();
		this.row = row;
		this.intensity = intensity;
	}

	public float getAngle() {
		return angle;
	}

	public void setAngle(float angle) {
		this.angle = angle;
	}

	@Override
	public String toString() {
		String out = "";
		for (int ii = 1; ii < row; ii+=3) {
			out += " ";
		}
		return out + "Sample [angle=" + angle + ", column=" + column + ", distance="
				+ distance + ", intensity=" + intensity + ", row=" + row + "]";
	}

	public int getColumn() {
		return column;
	}


	public void setColumn(int column) {
		this.column = column;
	}

	public float getRow() {
		return row;
	}

	public void setRow(float row) {
		this.row = row;
	}

	public float getDistance() {
		return distance;
	}

	public void setDistance(float distance) {
		this.distance = distance;
	}

	public void setIntensity(float intensity) {
		this.intensity = intensity;
	}

	public float getIntensity() {
		return intensity;
	}

	public Position getPosition() {
		Position pos = new Position();

		pos.x = (float) (Math.sin(Math.toRadians(this.angle)) * this.distance);
		pos.y = (float) (Math.cos(Math.toRadians(this.angle)) * this.distance);

		return pos;
	}

	@Override
	public int compareTo(Sample o) {
		return (int) (o.getIntensity() - this.intensity);
	}

}
