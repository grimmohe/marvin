package org.cbase.marvin.log;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.EventQueue;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.GridLayout;
import java.awt.Image;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.image.BufferedImage;
import java.awt.image.Raster;
import java.io.IOException;
import java.util.List;

import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTabbedPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.JToolBar;
import javax.swing.UIManager;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;

import org.cbase.marvin.map.Position;
import org.cbase.marvin.sample.Sample;
import org.cbase.marvin.util.CalcUtil;



public class Viewer {

	private JFrame frame;
	private final JToolBar toolBar = new JToolBar();
	private JTextField txtLocalhost;

	private DrawingLoggerCallback draw;
	private LoggerClient logger;
	private Client client;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					Viewer window = new Viewer();
					window.frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	/**
	 * Create the application.
	 */
	public Viewer() {
		initialize();
	}

	/**
	 * Initialize the contents of the frame.
	 */
	private void initialize() {
		frame = new JFrame();
		frame.setBounds(100, 100, 450, 300);
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.getContentPane().add(toolBar, BorderLayout.NORTH);

		txtLocalhost = new JTextField();
		txtLocalhost.setText("localhost:3001");
		toolBar.add(txtLocalhost);
		txtLocalhost.setColumns(10);

		JButton btnConnect = new JButton("Connect");
		toolBar.add(btnConnect);

		JButton btnDisconnect = new JButton("Disconnect");
		toolBar.add(btnDisconnect);

		JButton btnCamSave = new JButton("CamSave");
		toolBar.add(btnCamSave);
		
		JTabbedPane tabbedPane = new JTabbedPane(JTabbedPane.TOP);
		frame.getContentPane().add(tabbedPane, BorderLayout.CENTER);

		JPanel connectionPanel = new JPanel();
		tabbedPane.addTab("Connection", null, connectionPanel, null);
		connectionPanel.setLayout(new GridLayout(1, 0, 0, 0));

		JTextArea textArea = new JTextArea();
		textArea.setTabSize(4);
		textArea.setEditable(false);
		connectionPanel.add(textArea);

		JPanel rawPanel = new JPanel();
		FlowLayout fl_rawPanel = (FlowLayout) rawPanel.getLayout();
		fl_rawPanel.setAlignment(FlowLayout.LEFT);
		tabbedPane.addTab("Raw", null, rawPanel, null);

		JPanel sampleListPanel = new JPanel();
		sampleListPanel.setBackground(UIManager.getColor("Panel.background"));
		tabbedPane.addTab("Samples", null, sampleListPanel, null);

		JPanel nodePanel = new JPanel();
		nodePanel.setBackground(UIManager.getColor("Panel.background"));
		tabbedPane.addTab("Nodes", null, nodePanel, null);

		JCheckBox checkRed = new JCheckBox("Red");
		checkRed.setFont(new Font("Dialog", Font.PLAIN, 10));
		rawPanel.add(checkRed);

		JCheckBox checkIntensity = new JCheckBox("Intensity");
		checkIntensity.setFont(new Font("Dialog", Font.PLAIN, 10));
		rawPanel.add(checkIntensity);

		this.draw = new DrawingLoggerCallback(rawPanel, checkRed, checkIntensity, sampleListPanel, nodePanel, this);
		this.logger = new LoggerClient(this.draw);
		this.client = new Client(this.logger);

		btnConnect.addActionListener(new Connector(this.client, this.draw));
		btnDisconnect.addActionListener(new Disconnector(this.client));
		btnCamSave.addActionListener(new CamSaver(this.client));
		tabbedPane.addChangeListener(new TabChange(this.draw));
	}

	public Client getClient() {
		return client;
	}

}

class Connector implements ActionListener {

	private Client client;
	private DrawingLoggerCallback draw;

	public Connector(Client client, DrawingLoggerCallback draw) {
		super();
		this.client = client;
		this.draw = draw;
	}

	@Override
	public void actionPerformed(ActionEvent e) {
		client.connect();
		draw.redraw();
	}

}

class Disconnector implements ActionListener {

	private Client client;

	public Disconnector(Client client) {
		super();
		this.client = client;

	}

	@Override
	public void actionPerformed(ActionEvent e) {
		client.disconnect();
	}

}

class CamSaver implements ActionListener {

	private Client client;

	public CamSaver(Client client) {
		super();
		this.client = client;

	}

	@Override
	public void actionPerformed(ActionEvent e) {
		try {
			client.camSaveCommand();
		} catch (IOException e1) {
			e1.printStackTrace();
		}
	}

}

class DrawingLoggerCallback implements ClientLoggerCallback {

	private Viewer viewer;

	JPanel rawImagePanel;
	BufferedImage rawImage;
	JCheckBox rawRed;
	JCheckBox rawIntensity;
	List<Sample> rawRowNodes;

	JPanel sampleListPanel;
	List<Sample> sampleList;
	float sampleListRadius;

	JPanel nodePanel;
	List<Sample> nodes;
	float nodeRadius;

	public DrawingLoggerCallback(JPanel rawImagePanel, JCheckBox red, JCheckBox intensity, JPanel sampleListPanel, JPanel nodePanel, Viewer viewer) {
		super();
		this.rawImagePanel = rawImagePanel;
		this.rawRed = red;
		this.rawIntensity = intensity;
		this.sampleListPanel = sampleListPanel;
		this.nodePanel = nodePanel;
		this.viewer = viewer;
	}

	public void redraw() {
		try {
			Client client = viewer.getClient();
			if(client != null) {
				client.setWichesRawImage(this.rawImagePanel.isVisible());
				client.setWichesSampleList(this.sampleListPanel.isVisible()
						|| this.rawImagePanel.isVisible());
				client.setWichesNodeList(this.nodePanel.isVisible());
			}
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		// this.newSampleList(null);
		// this.newNodeList(null);
	}

	@Override
	public void newSampleList(List<Sample> samples) {

		if (samples != null)
			this.sampleList = samples;

		if (!this.sampleListPanel.isVisible() || this.sampleList == null
				|| this.sampleList.size() == 0)
			return;

		Image img = this.sampleListPanel.createImage(this.sampleListPanel
				.getWidth(), this.sampleListPanel.getHeight());

		Graphics g = img.getGraphics();

		float scale = Math.max(this.sampleListRadius
				/ this.sampleListPanel.getHeight(), this.sampleListRadius
				/ (this.sampleListPanel.getWidth() / 2));

		float newRad = 1;
		int startX = this.sampleListPanel.getWidth() / 2;
		int startY = this.sampleListPanel.getHeight();

		g.clearRect(0, 0, sampleListPanel.getWidth(), sampleListPanel
				.getHeight());

		g.drawString("#: " + this.sampleList.size(), 0, g.getFontMetrics()
				.getHeight());
		g.drawString("Radius: " + this.sampleListRadius, 0, 2 + (g
				.getFontMetrics().getHeight() * 2));

		Position lastPos = null;

		for (Sample sample : this.sampleList) {
			newRad = Math.max(newRad, sample.getDistance());

			Position pos = sample.getPosition();

			if (lastPos != null) {
				g.drawLine((int) (startX + lastPos.x / scale),
						(int) (startY - lastPos.y / scale),
						(int) (startX + pos.x / scale), (int) (startY - pos.y
								/ scale));
			}

			lastPos = pos;
		}

		this.sampleListPanel.getGraphics().drawImage(img, 0, 0, null);

		this.sampleListRadius = newRad;
	}

	@Override
	public void newNodeList(List<Sample> nodes) {

		if (nodes != null)
			this.nodes = nodes;

		if (!this.nodePanel.isVisible() || this.nodes == null)
			return;

		Image img = this.sampleListPanel.createImage(this.nodePanel.getWidth(),
				this.nodePanel.getHeight());

		Graphics g = img.getGraphics();

		float scale = Math.max(this.nodeRadius / this.nodePanel.getHeight(),
				this.nodeRadius / (this.nodePanel.getWidth() / 2));

		float newRad = 1;
		int startX = this.nodePanel.getWidth() / 2;
		int startY = this.nodePanel.getHeight();

		g.clearRect(0, 0, this.nodePanel.getWidth(), this.nodePanel
				.getHeight());

		g.drawString("#: " + this.nodes.size(), 0, g.getFontMetrics()
				.getHeight());
		g.drawString("Radius: " + this.nodeRadius, 0, 2 + (g.getFontMetrics()
				.getHeight() * 2));

		Position lastPos = null;

		for (Sample node : this.nodes) {
			newRad = Math.max(newRad, node.getDistance());

			Position pos = node.getPosition();

			if (lastPos != null) {
				g.drawLine((int) (startX + lastPos.x / scale),
						(int) (startY - lastPos.y / scale),
						(int) (startX + pos.x / scale), (int) (startY - pos.y
								/ scale));
			}

			lastPos = pos;
		}

		this.nodePanel.getGraphics().drawImage(img, 0, 0, null);

		this.nodeRadius = newRad;

	}

	@Override
	public void newRawImage(BufferedImage deserializedRawImage) {

		if (deserializedRawImage != null) this.rawImage = deserializedRawImage;

		if (!this.rawImagePanel.isVisible() || this.rawImage == null) return;

		if (this.rawRed.isSelected()) {
			Raster r = this.rawImage.getRaster();

			for (int x=0; x<r.getWidth(); x++) {
				for (int y=0; y<r.getHeight(); y++) {
					int[] pixel = r.getPixel(x, y, (int[])null);
					this.rawImage.setRGB(x, y, CalcUtil.getRed(pixel[0], pixel[1], pixel[2]) << 16);
				}
			}
		}

		if (this.sampleList != null) {
			Graphics g = this.rawImage.getGraphics();
			g.setColor(new Color(0, 255, 255));
			for (Sample sample: this.sampleList) {
				int intensity = (int) sample.getIntensity();
				if (!this.rawIntensity.isSelected()) {
					intensity = 2;
				}
				g.drawOval(
						sample.getColumn() - (intensity / 2),
						(int)sample.getRow() - (intensity / 2),
						intensity,
						intensity
						);
			}
		}

		this.rawImagePanel.getGraphics().drawImage
			( this.rawImage,
			  0, this.rawRed.getX() + this.rawRed.getHeight(), this.nodePanel.getWidth(), this.nodePanel.getHeight(),
			  0, 0, this.rawImage.getWidth(null), this.rawImage.getHeight(null),
			  null);
	}

	@Override
	public void newRowNodes(List<Sample> deserializeSampleList) {

		if (deserializeSampleList != null) this.rawRowNodes = deserializeSampleList;

	}

}

class TabChange implements ChangeListener {

	private DrawingLoggerCallback draw;

	public TabChange(DrawingLoggerCallback draw) {
		super();
		this.draw = draw;
	}

	@Override
	public void stateChanged(ChangeEvent e) {
		this.draw.redraw();
	}

}
