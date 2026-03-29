import sys
import os
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QSlider, QMessageBox, QStatusBar, QCheckBox)
from PyQt6.QtCore import Qt, QUrl, QTimer
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
        hbox_bottom = QHBoxLayout()
        self.btn_trim = QPushButton("Trim and Save Video")
        self.btn_trim.setEnabled(False)
        self.btn_trim.setMinimumHeight(40)
        
        self.cb_remove_audio = QCheckBox("Remove Audio")
        
        hbox_bottom.addWidget(self.btn_trim, stretch=2)
        hbox_bottom.addWidget(self.cb_remove_audio)
        vbox.addLayout(hbox_bottom)
        
        # Tools controls
        hbox_tools = QHBoxLayout()
        self.btn_merge = QPushButton("Merge Videos...")
        hbox_tools.addWidget(self.btn_merge)
        vbox.addLayout(hbox_tools)
        
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
        self.btn_merge.clicked.connect(self.merge_videos)
        
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
            self.media_player.stop()  # Stop playback before loading a new file
            self.media_player.setSource(QUrl()) # Clear pipeline to prevent Linux GStreamer deadlock
            
            # Defer loading to the event loop so the backend has time to stop rendering
            QTimer.singleShot(50, lambda: self._load_new_video(file_path))

    def _load_new_video(self, file_path):
            self.video_path = file_path
            self.lbl_file.setText(os.path.basename(file_path))
            self.lbl_file.setStyleSheet("color: black;")
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            
            self.start_time_ms = 0
            self.end_time_ms = 0
            self.lbl_start.setText("Start: 00:00:00.000")
            self.lbl_end.setText("End: --:--:--.---")
            self.slider.setValue(0)
            self.btn_trim.setEnabled(True)
            self.status_bar.showMessage(f"Loaded {os.path.basename(file_path)}")
            # Autoplay the new video
            self.media_player.play()

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
        # We use -ss before -i for fast seek, and -t for accurate duration
        start_sec = self.start_time_ms / 1000.0
        end_sec = self.end_time_ms / 1000.0
        duration = end_sec - start_sec

        cmd = [
            "ffmpeg",
            "-y", # overwrite output
            "-ss", str(start_sec),
            "-i", self.video_path,
            "-t", str(duration),
            "-c", "copy"
        ]
        
        if self.cb_remove_audio.isChecked():
            cmd.append("-an")
            
        cmd.append(output_path)
        
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

    def merge_videos(self):
        file_paths = []
        
        # 1. Ask about currently open video
        if self.video_path:
            reply = QMessageBox.question(
                self, "Include Current Video",
                "Do you want to include the currently open video as the first video to merge?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                file_paths.append(self.video_path)
                
        # 2. Select files natively without a while True loop
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select videos to merge (Hold Ctrl/Cmd to select multiple)", 
            "", "Video Files (*.mp4 *.mkv *.avi *.mov *.webm)"
        )
        
        if paths:
            file_paths.extend(paths)

        if len(file_paths) < 2:
            if file_paths: # if they only ended up with 1
                QMessageBox.warning(self, "Merge Videos", "Please select at least 2 videos to merge.")
            return

        # 3. Get save destination
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged Video", 
            os.path.splitext(file_paths[0])[0] + "_merged.mp4", 
            "Video Files (*.mp4 *.mkv *.avi)"
        )
        if not output_path:
            return

        self.status_bar.showMessage("Merging videos... Please wait. (The app will pause during this)")
        QApplication.processEvents() # Force UI to update before subprocess blocks

        # 4. Create the temp file list
        list_file_path = os.path.join(os.path.dirname(output_path), "merge_list_tmp.txt")
        try:
            with open(list_file_path, "w", encoding="utf-8") as f:
                for path in file_paths:
                    # Force forward slashes to prevent FFmpeg Windows path errors
                    safe_path = path.replace('\\', '/')
                    # Escape single quotes in path
                    safe_path = safe_path.replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")

            cmd = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file_path,
                "-c", "copy"
            ]
            
            if self.cb_remove_audio.isChecked():
                cmd.append("-an")
                
            cmd.append(output_path)

            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.status_bar.showMessage(f"Successfully saved to {os.path.basename(output_path)}", 5000)
                QMessageBox.information(self, "Success", f"Videos merged successfully!\nSaved to: {output_path}")
            else:
                self.status_bar.showMessage("Error merging videos.", 5000)
                
                # Check for common mismatch errors in stderr
                stderr_lower = result.stderr.lower()
                if "non-monotonous dts" in stderr_lower or "different" in stderr_lower:
                    QMessageBox.critical(self, "Codec/Resolution Mismatch", 
                        "Merge Failed.\n\nBecause this tool uses fast-merging (-c copy), all selected videos MUST have the exact same resolution, framerate, and codec. If they are different, FFmpeg cannot stitch them together.\n\nFFmpeg Details:\n" + result.stderr[-400:])
                else:
                    QMessageBox.critical(self, "Error", f"FFmpeg error:\n{result.stderr[-1000:]}")
                    
        except Exception as e:
            self.status_bar.showMessage("Error merging videos.", 5000)
            QMessageBox.critical(self, "Exception", f"Could not merge videos:\n{str(e)}")
        finally:
            if os.path.exists(list_file_path):
                try:
                    os.remove(list_file_path)
                except:
                    pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoTrimmer()
    window.show()
    sys.exit(app.exec())