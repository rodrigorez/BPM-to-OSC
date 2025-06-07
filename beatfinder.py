import numpy as np
import pyaudio
from collections import deque
from aubio import tempo


#local
import osc_client



class BeatPrinter:
    def __init__(self):
        self.state: int = 0
        self.spinner = "▚▞"

    def print_bpm(self, bpm: float) -> None:
        print(f"{self.spinner[self.state]}\t{bpm:.1f} BPM")

        self.state = (self.state + 1) % len(self.spinner)


class BeatDetector:

    def __init__(self, client: osc_client.OSCclient, audio_device_index: int = 1, parent=None, buf_size: int = 128):
        # arguments
        self.client = client  # OSC client
        self.audio_device_index = audio_device_index
        self.parent = parent  # MainFrame
        self.buf_size: int = buf_size  # buffer size
        
        # variables
        self.blink = 0  # blinking state flag
        self.bpm = 128
        self.beat_counter = 0 # for live beat divider
        self.SAMPLERATE: int = 44100
        self.level_reset = None  # Timer for resetting level
        self.level_queue = deque(maxlen=20)  # RMS Level queue
        self.p: pyaudio.PyAudio = pyaudio.PyAudio()
        self.tempo = tempo("default", self.buf_size * 2, self.buf_size, self.SAMPLERATE)
        self.stream = None # Initialize stream attribute

        try:
            # Callback to GUI
            if self.parent is not None:
                self.stream: pyaudio.Stream = self.p.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=self.SAMPLERATE,
                    input=True,
                    input_device_index=self.audio_device_index,
                    frames_per_buffer=self.buf_size,
                    stream_callback=self._GUI_callback
                )

            # Callback to Console (standalone)
            else:
                self.stream: pyaudio.Stream = self.p.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=self.SAMPLERATE,
                    input=True,
                    frames_per_buffer=self.buf_size,
                    stream_callback=self._STANDALONE_callback
                )
                # init output class
                self.spinner = BeatPrinter()
        except Exception as e:
            print(f"ERRO em BeatDetector: Não foi possível abrir o stream de áudio. Dispositivo: {self.audio_device_index}. Erro: {e}")
            self.stream = None # Ensure stream is None if opening failed
            # If running with GUI, inform the parent as well
            if self.parent and hasattr(self.parent, 'show_error_message'):
                self.parent.show_error_message(f"Falha ao abrir stream de áudio no dispositivo {self.audio_device_index}.\nVerifique as configurações de áudio.\nErro: {e}")



    def _GUI_callback(self, in_data, frame_count, time_info, status):
        """Callback for pyaudio stream\n
        Calculates BPM and sends them to the GUI\n
        Calculates RMS Level into variable self.level to fetch by PeakMeter\n
        Args:
            in_data (array): data from pyaudio stream
            frame_count (int): number of frames in in_data
            time_info (): time info from pyaudio stream
            status (): status from pyaudio stream\n
        Returns:
            None, paContinue: Tells pyaudio to continue streaming
        """

        signal = np.frombuffer(in_data, dtype=np.float32)
        beat = self.tempo(signal)

        # Calculate RMS Level for every frame and add it to a circular buffer
        self.level_queue.append(int(np.sqrt(signal.dot(signal)/signal.size) * 200))  # 9,0ms
        """alternative RMS functions:
        # cur = np.sqrt((signal*signal).sum()/(1.*len(signal)))*10000 #10,1ms
        #self.level = np.sqrt(signal.dot(signal)/signal.size) * 10000  # 9,0ms
        # cur = np.sqrt(np.mean(np.square(signal))) * 10000 #23,5ms
        # cur = np.max(np.abs(signal))*10000 #12,0ms"""
        
        # if beat is detected
        if beat[0]:
            
            self.beat_counter += 1
            # extract bpm
            self.bpm = round(self.tempo.get_bpm())

            if self.bpm > 20 and self.bpm < 200 and self.parent.running:
                if self.parent.sync:

                    # SEND to osc and BOTH display if sync is on
                    # Inform Main_Frame about the detected BPM so it can update self.send_bpm thread-safely
                    self.parent.process_detected_beat(self.bpm)
                                        
                    self.parent.update_bpm_display(self.bpm, send_to="live", Blink=True)
                    
                    # Read beat_divider from parent thread-safely for consistent sending
                    current_beat_divider = 1 # Default value
                    # Accessing parent's lock directly is not ideal.
                    # A better way would be for parent to expose beat_divider via a thread-safe getter
                    # or for process_detected_beat to also handle the OSC sending logic based on sync.
                    # For now, we assume beat_divider read from parent is "recent enough"
                    # or that its changes are infrequent compared to beat detection.
                    # This is a potential area for further refinement if strict sync is needed for beat_divider.
                    with self.parent.bpm_lock: # Acquire lock to read beat_divider
                        current_beat_divider = self.parent.beat_divider

                    if current_beat_divider == 1:
                        self.client.send_osc(self.parent.config['OSC']['BPM_ADRESS'], self.bpm, map_to_resolume=True)
                        self.parent.update_bpm_display(self.bpm, send_to="send", Blink=True) # send bpm to send display
                        self.parent.next_led()
                    
                    elif (self.beat_counter + 1) % current_beat_divider == 0:
                        # Use self.bpm directly as it's the raw detected value.
                        # The parent.send_bpm is updated by process_detected_beat.
                        # The division happens for sending purposes here.
                        divided_bpm = self.bpm // current_beat_divider
                        self.client.send_osc(self.parent.config['OSC']['BPM_ADRESS'], divided_bpm, map_to_resolume=True)
                        self.parent.update_bpm_display(divided_bpm, send_to="send", Blink=True) # send bpm to send display
                        self.parent.next_led()

                        
                    # BLINK resync button to beat when syncing (tap thread taking over when no sync)
                    #self.parent.button_resync.BackgroundColour = (220, 220, 220) if self.blink else self.parent.bg_grey
                    #self.blink = not self.blink
                    

                else:
                    # SEND only to LIVE display if sync is off
                    self.parent.update_bpm_display(self.bpm, send_to="live", Blink=False)
                    
            if self.beat_counter == 4:
                self.beat_counter = 0

        # terminate stream if running is stopped
        return (None, pyaudio.paContinue) if self.parent.running else (None, pyaudio.paComplete)

    def _STANDALONE_callback(self, in_data, frame_count, time_info, status):
        signal = np.frombuffer(in_data, dtype=np.float32)
        beat = self.tempo(signal)
        if beat[0]:
            self.spinner.print_bpm(self.tempo.get_bpm())
        return None, pyaudio.paContinue  # Tell pyAudio to continue

    def resync_bar(self):
        """Send resync command to Resolume"""
        self.client.send_osc(self.parent.config['OSC']['RESYNC_BAR_ADRESS'], 1)

    def __del__(self):
        """Close pyaudio stream and terminate pyaudio
        """
        if self.level_reset is not None:
            self.level_reset.cancel()
        if self.stream:
            self.stream.close()
        if self.p: # PyAudio instance might not be fully initialized if error occurs early
            self.p.terminate()

if __name__ == "__main__":
    import os
    import time
    # import signal # Required for signal.pause() on Unix-like systems

    client = osc_client.OSCclient("127.0.0.1", 7000)
    bd = BeatDetector(client, audio_device_index=0, buf_size=128) # Assuming device index 0 for standalone testing
    if bd.stream: # Only proceed if stream was successfully opened
        try:
            print("BeatDetector iniciado. Pressione Ctrl+C para sair.")
            # Audio processing happens in separate thread, so put this thread to sleep
            if os.name == 'nt':  # Windows is not able to pause the main thread :(
                while True:
                    time.sleep(1)
            else:
                # signal.pause() # This would require import signal
                while True: # Using a simple loop for broader compatibility without new import
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nFechando BeatDetector...")
        finally:
            # print(sum(bd.timings)/len(bd.timings)) # timings attribute does not exist
            del bd # Ensure __del__ is called
    else:
        print("BeatDetector não pôde ser iniciado devido a um erro no stream de áudio.")
