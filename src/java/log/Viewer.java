package log;

import java.awt.BorderLayout;
import java.awt.EventQueue;
import java.awt.Graphics;
import java.awt.GridLayout;
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

public class Viewer {

	private JFrame	frame;
	private final JToolBar toolBar = new JToolBar();
	private JTextField txtLocalhost;
	private JPanel	sampleListPanel;

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

		sampleListPanel = new JPanel();
		sampleListPanel.setBackground(UIManager.getColor("Panel.background"));
		tabbedPane.addTab("Samples", null, sampleListPanel, null);

		JPanel nodePanel = new JPanel();
		tabbedPane.addTab("Nodes", null, nodePanel, null);

		this.draw = new Draw(sampleListPanel);
		this.logger = new Logger(this.draw);
		this.client = new Client(this.logger);

		btnConnect.addActionListener(new Connector(this.client));
		btnDisconnect.addActionListener(new Disconnector(this.client));
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

	public Draw(JPanel sampleListPanel) {
		super();
		this.sampleListPanel = sampleListPanel;
	}

	@Override
	public void newSampleList(List<Sample> samples) {

		if (samples != null) this.sampleList = samples;

		if (!this.sampleListPanel.isVisible()) return;

		Graphics g = this.sampleListPanel.getGraphics();

		float scale
			= Math.max( this.sampleListRadius / this.sampleListPanel.getHeight(),
						this.sampleListRadius / (sampleListPanel.getWidth()/2) );

		float newRad = 1;
		int startX = this.sampleListPanel.getWidth()/2;
		int startY = this.sampleListPanel.getHeight();

		g.clearRect(0, 0, sampleListPanel.getWidth(), sampleListPanel.getHeight());

		g.drawString("Radius: " + this.sampleListRadius, 0, g.getFontMetrics().getHeight());

		for (Sample sample : samples) {
			newRad = Math.max(newRad, sample.getDistance());

			Position pos = sample.getPosition();

			g.drawLine
				( startX,
				  startY,
				  (int) (startX + pos.x / scale),
				  (int) (startY - pos.y / scale) );

		}

		this.sampleListRadius = newRad;
	}


}

