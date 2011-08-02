package log;

import java.awt.BorderLayout;
import java.awt.EventQueue;
import java.awt.Graphics;
import java.awt.GridLayout;
import java.awt.Image;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.List;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTabbedPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.JToolBar;
import javax.swing.UIManager;

import map.Position;
import sample.Sample;
import javax.swing.event.ChangeListener;
import javax.swing.event.ChangeEvent;

public class Viewer {

	private JFrame	frame;
	private final JToolBar toolBar = new JToolBar();
	private JTextField txtLocalhost;

	private Draw draw;
	private Logger logger;
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

		JTabbedPane tabbedPane = new JTabbedPane(JTabbedPane.TOP);
		frame.getContentPane().add(tabbedPane, BorderLayout.CENTER);

		JPanel connectionPanel = new JPanel();
		tabbedPane.addTab("Connection", null, connectionPanel, null);
		connectionPanel.setLayout(new GridLayout(1, 0, 0, 0));

		JTextArea textArea = new JTextArea();
		textArea.setTabSize(4);
		textArea.setEditable(false);
		connectionPanel.add(textArea);

		JPanel sampleListPanel = new JPanel();
		sampleListPanel.setBackground(UIManager.getColor("Panel.background"));
		tabbedPane.addTab("Samples", null, sampleListPanel, null);

		JPanel nodePanel = new JPanel();
		nodePanel.setBackground(UIManager.getColor("Panel.background"));
		tabbedPane.addTab("Nodes", null, nodePanel, null);

		this.draw = new Draw(sampleListPanel, nodePanel);
		this.logger = new Logger(this.draw);
		this.client = new Client(this.logger);

		btnConnect.addActionListener(new Connector(this.client));
		btnDisconnect.addActionListener(new Disconnector(this.client));
		tabbedPane.addChangeListener(new TabChange(this.draw));
	}

}

class Connector implements ActionListener {

	private Client client;

	public Connector(Client client) {
		super();
		this.client = client;

	}

	@Override
	public void actionPerformed(ActionEvent e) {
		client.connect();
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

class Draw implements ClientLoggerCallback {

	JPanel sampleListPanel;
	List<Sample> sampleList;
	float sampleListRadius;

	JPanel nodePanel;
	List<Sample> nodes;
	float nodeRadius;

	public Draw(JPanel sampleListPanel, JPanel nodePanel) {
		super();
		this.sampleListPanel = sampleListPanel;
		this.nodePanel = nodePanel;
	}

	public void redraw() {
		this.newSampleList(null);
		this.newNodeList(null);
	}

	@Override
	public void newSampleList(List<Sample> samples) {

		if (samples != null) this.sampleList = samples;

		if (!this.sampleListPanel.isVisible() || this.sampleList == null) return;

		Image img = this.sampleListPanel.createImage(this.sampleListPanel.getWidth(), this.sampleListPanel.getHeight());

		Graphics g = img.getGraphics();

		float scale
			= Math.max( this.sampleListRadius / this.sampleListPanel.getHeight(),
						this.sampleListRadius / (this.sampleListPanel.getWidth()/2) );

		float newRad = 1;
		int startX = this.sampleListPanel.getWidth()/2;
		int startY = this.sampleListPanel.getHeight();

		g.clearRect(0, 0, sampleListPanel.getWidth(), sampleListPanel.getHeight());

		g.drawString("#: " + this.sampleList.size(), 0, g.getFontMetrics().getHeight());
		g.drawString("Radius: " + this.sampleListRadius, 0, 2+(g.getFontMetrics().getHeight()*2));

		Position lastPos = null;

		for (Sample sample : this.sampleList) {
			newRad = Math.max(newRad, sample.getDistance());

			Position pos = sample.getPosition();

			if (lastPos != null) {
				g.drawLine
					( (int) (startX + lastPos.x / scale),
					  (int) (startY - lastPos.y / scale),
					  (int) (startX + pos.x / scale),
					  (int) (startY - pos.y / scale) );
			}

			lastPos = pos;
		}

		this.sampleListPanel.getGraphics().drawImage(img, 0, 0, null);

		this.sampleListRadius = newRad;
	}

	@Override
	public void newNodeList(List<Sample> nodes) {

		if (nodes != null) this.nodes = nodes;

		if (!this.nodePanel.isVisible() || this.nodes == null) return;

		Image img = this.sampleListPanel.createImage(this.nodePanel.getWidth(), this.nodePanel.getHeight());

		Graphics g = img.getGraphics();

		float scale
			= Math.max( this.nodeRadius / this.nodePanel.getHeight(),
						this.nodeRadius / (this.nodePanel.getWidth()/2) );

		float newRad = 1;
		int startX = this.nodePanel.getWidth()/2;
		int startY = this.nodePanel.getHeight();

		g.clearRect(0, 0, this.nodePanel.getWidth(), this.nodePanel.getHeight());

		g.drawString("Radius: " + this.nodeRadius, 0, g.getFontMetrics().getHeight());

		Position lastPos = null;

		for (Sample node : this.nodes) {
			newRad = Math.max(newRad, node.getDistance());

			Position pos = node.getPosition();

			if (lastPos != null) {
				g.drawLine
					( (int) (startX + lastPos.x / scale),
					  (int) (startY - lastPos.y / scale),
					  (int) (startX + pos.x / scale),
					  (int) (startY - pos.y / scale) );
			}

			lastPos = pos;
		}

		this.nodePanel.getGraphics().drawImage(img, 0, 0, null);

		this.nodeRadius = newRad;

	}

}

class TabChange implements ChangeListener {

	private Draw draw;

	public TabChange(Draw draw) {
		super();
		this.draw = draw;
	}

	@Override
	public void stateChanged(ChangeEvent e) {
		this.draw.redraw();
	}

}

