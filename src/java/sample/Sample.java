package sample;

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

	@Override
	public int compareTo(Sample o) {
		return (int) (o.getIntensity() - this.intensity);
	}

}
