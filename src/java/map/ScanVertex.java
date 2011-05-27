package map;

public class ScanVertex extends Vertex {

	public Position pos = new Position();

	public float getDistance (ScanVertex second) {
		return (float) Math.sqrt(Math.pow(this.pos.x - second.pos.x, 2)
								 + Math.pow(this.pos.y - second.pos.y, 2));
	}

}
