import sys
import os
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QSlider, QMessageBox, QStatusBar)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

class VideoTrimmer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fast Video Trimmer")
        self.resize(800, 600)
        
        self.video_path = None
        self.start_time_ms = 0
        self.end_time_ms = 0
        self.total_duration_ms = 0
        
        # Setup Multimedia
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        vbox = QVBoxLayout()
        
        # Top controls
        hbox_top = QHBoxLayout()
        self.btn_open = QPushButton("Open Video...")
        self.lbl_file = QLabel("No file selected")
        self.lbl_file.setStyleSheet("color: gray;")
        hbox_top.addWidget(self.btn_open)
        hbox_top.addWidget(self.lbl_file)
        hbox_top.addStretch()
        vbox.addLayout(hbox_top)
        
        # Video Area
        vbox.addWidget(self.video_widget, stretch=1)
        
        # Playback controls
        hbox_play = QHBoxLayout()
        self.btn_play = QPushButton("Play")
        self.lbl_current_time = QLabel("00:00:00")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.lbl_total_time = QLabel("00:00:00")
        
        hbox_play.addWidget(self.btn_play)
        hbox_play.addWidget(self.lbl_current_time)
        hbox_play.addWidget(self.slider)
        hbox_play.addWidget(self.lbl_total_time)
        vbox.addLayout(hbox_play)
        
        # Trim controls
        hbox_trim = QHBoxLayout()
        self.btn_set_start = QPushButton("Set Start [")
        self.lbl_start = QLabel("Start: 00:00:00.000")
        
        self.btn_set_end = QPushButton("Set End ]")
        self.lbl_end = QLabel("End: --:--:--.---")
        
        hbox_trim.addWidget(self.btn_set_start)
        hbox_trim.addWidget(self.lbl_start)
        hbox_trim.addSpacing(20)
        hbox_trim.addWidget(self.btn_set_end)
        hbox_trim.addWidget(self.lbl_end)
        hbox_trim.addStretch()
        vbox.addLayout(hbox_trim)
        
        # Bottom controls
        self.btn_trim = QPushButton("Trim and Save Video")
        self.btn_trim.setEnabled(False)
        self.btn_trim.setMinimumHeight(40)
        vbox.addWidget(self.btn_trim)
        
        central_widget.setLayout(vbox)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_signals(self):
        self.btn_open.clicked.connect(self.open_file)
        self.btn_play.clicked.connect(self.play_pause)
        self.btn_set_start.clicked.connect(self.set_start_time)
        self.btn_set_end.clicked.connect(self.set_end_time)
        self.btn_trim.clicked.connect(self.trim_video)
        
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.state_changed)
        
        self.slider.sliderMoved.connect(self.set_position)

    def format_time(self, ms, show_ms=False):
        seconds = (ms // 1000) % 60
        minutes = (ms // 60000) % 60
        hours = ms // 3600000
        millis = ms % 1000
        if show_ms:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "", "Video Files (*.mp4 *.avi *.mkv *.mov *.webm)"
        )
        if file_path:
            self.video_path = file_path
            self.lbl_file.setText(os.path.basename(file_path))
            self.lbl_file.setStyleSheet("color: black;")
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            
            self.start_time_ms = 0
            self.end_time_ms = 0
            self.lbl_start.setText("Start: 00:00:00.000")
            self.lbl_end.setText("End: --:--:--.---")
            self.btn_trim.setEnabled(True)
            self.status_bar.showMessage(f"Loaded {os.path.basename(file_path)}")
            # Autoplay to initialize properly sometimes needed
            self.media_player.play()
            self.media_player.pause()

    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            if self.media_player.source().isEmpty():
                return
            self.media_player.play()

    def state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play.setText("Pause")
        else:
            self.btn_play.setText("Play")

    def position_changed(self, position):
        self.slider.setValue(position)
        self.lbl_current_time.setText(self.format_time(position))
        
        # Optional: Auto-pause if we hit the end bound during preview
        if self.end_time_ms > 0 and position >= self.end_time_ms and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)
        self.lbl_total_time.setText(self.format_time(duration))
        self.total_duration_ms = duration
        if self.end_time_ms == 0:
            self.end_time_ms = duration
            self.lbl_end.setText(f"End: {self.format_time(duration, True)}")

    def set_position(self, position):
        self.media_player.setPosition(position)

    def set_start_time(self):
        pos = self.media_player.position()
        if self.end_time_ms > 0 and pos >= self.end_time_ms:
            QMessageBox.warning(self, "Invalid Start Time", "Start time must be before end time.")
            return
            
        self.start_time_ms = pos
        self.lbl_start.setText(f"Start: {self.format_time(pos, True)}")

    def set_end_time(self):
        pos = self.media_player.position()
        if pos <= self.start_time_ms:
            QMessageBox.warning(self, "Invalid End Time", "End time must be after start time.")
            return
            
        self.end_time_ms = pos
        self.lbl_end.setText(f"End: {self.format_time(pos, True)}")

    def trim_video(self):
        if not self.video_path:
            return
            
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Trimmed Video", 
            os.path.splitext(self.video_path)[0] + "_trimmed.mp4", 
            "Video Files (*.mp4 *.mkv *.avi)"
        )
        if not output_path:
            return

        self.status_bar.showMessage("Trimming video... Please wait.")
        QApplication.processEvents()

        # Build ffmpeg command
        # -ss start_time -to end_time -i input -c copy output
        # Format ms to seconds for ffmpeg
        start_sec = self.start_time_ms / 1000.0
        end_sec = self.end_time_ms / 1000.0

        cmd = [
            "ffmpeg",
            "-y", # overwrite output
            "-ss", str(start_sec),
            "-to", str(end_sec),
            "-i", self.video_path,
            "-c", "copy",
            output_path
        ]
        
        try:
            # We use subprocess.run so it runs synchronously and fast
            # We also capture output to avoid printing to console unless needed
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.status_bar.showMessage(f"Successfully saved to {os.path.basename(output_path)}", 5000)
                QMessageBox.information(self, "Success", f"Video trimmed successfully!\nSaved to: {output_path}")
            else:
                self.status_bar.showMessage("Error trimming video.", 5000)
                QMessageBox.critical(self, "Error", f"FFmpeg error:\n{result.stderr}")
                
        except Exception as e:
            self.status_bar.showMessage("Error trimming video.", 5000)
            QMessageBox.critical(self, "Exception", f"Could not trim video:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoTrimmer()
    window.show()
    sys.exit(app.exec())
