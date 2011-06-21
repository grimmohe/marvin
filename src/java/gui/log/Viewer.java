package gui.log;

import java.awt.EventQueue;
import java.awt.Graphics;

import javax.swing.JFrame;
import javax.swing.JToolBar;
import java.awt.BorderLayout;

import javax.swing.JComponent;
import javax.swing.JDesktopPane;
import javax.swing.JTabbedPane;
import javax.swing.JPanel;
import java.awt.SystemColor;
import javax.swing.UIManager;
import javax.swing.JButton;
import java.awt.GridLayout;
import javax.swing.JTextField;
import javax.swing.JTextArea;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;

public class Viewer {

	private JFrame	frame;
	private final JToolBar toolBar = new JToolBar();
	private JTextField txtLocalhost;

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

		JPanel samplePanel = new JPanel();
		samplePanel.setBackground(UIManager.getColor("Panel.background"));
		tabbedPane.addTab("Samples", null, samplePanel, null);

		JPanel nodePanel = new JPanel();
		tabbedPane.addTab("Nodes", null, nodePanel, null);

		btnConnect.addActionListener(new MyStarDrawer(samplePanel));
	}

}

class MyStarDrawer implements ActionListener {

	private JPanel panel;
	private Star star;
	private int count = 1;

	public MyStarDrawer(JPanel panel) {
		super();

		this.panel = panel;
	}

	@Override
	public void actionPerformed(ActionEvent e) {
		Graphics g = this.panel.getGraphics();
		int radius = this.panel.getHeight() / 2;

		for (double angle = 0; angle < Math.PI; angle = angle + Math.PI / 16) {
			double x1, x2, y1, y2;
			x1 = Math.cos(angle + this.count) * radius + radius;
			y1 = Math.sin(angle + this.count) * radius + radius;
			x2 = Math.cos(angle + Math.PI + this.count) * radius + radius;
			y2 = Math.sin(angle + Math.PI + this.count) * radius + radius;
			g.drawLine((int)x1, (int)y1, (int)x2, (int)y2);
		}

		this.count++;
	}

}

class Star extends JComponent {

	private int radius;

	public void paint(Graphics g) {

		System.out.println("debug");
	}
	public void setRadius(int radius) {
		this.radius = radius;
	}
}

