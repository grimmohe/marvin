package org.cbase.marvin.db;

import java.io.File;
import java.io.IOException;

import org.neo4j.graphdb.GraphDatabaseService;
import org.neo4j.graphdb.RelationshipType;
import org.neo4j.kernel.EmbeddedGraphDatabase;

public class Database {

	private static Database database;

	public static Database getInstance() {
		if (database==null)  database = new Database();

		return database;
	}

	public static boolean isInstantiated() {
		return database != null;
	}

	public static enum relation implements RelationshipType {
		WALL, INFO;
	}

	private GraphDatabaseService graphDb;
	private File databaseDir;

	private Database() {
		try {
			databaseDir = File.createTempFile("marvin", "");
			databaseDir.delete();
			databaseDir.mkdir();

			this.graphDb = new EmbeddedGraphDatabase(databaseDir.getCanonicalPath());
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	public void shutdownDatabase() {
		this.graphDb.shutdown();
		this.deleteFile(databaseDir);
	}

	private void deleteFile(File f) {
		File[] subs = f.listFiles();
		if (subs != null) {
			for (File subFile: subs) {
				deleteFile(subFile);
			}
		}

		f.delete();
	}
}
