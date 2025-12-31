# Real-Time Voice Changer

A real-time voice changer application with pitch shifting, formant shifting, and various audio effects.

## Features

- 🎤 **Real-time voice processing** - Low latency audio pipeline
- 🎵 **Pitch shifting** - Change voice pitch up to ±12 semitones
- 👩 **Formant shifting** - Change vocal characteristics (male/female)
- 🎛️ **Effects chain** - Reverb, chorus, distortion, compressor, delay
- 💾 **Presets** - Woman, Male, Child, Monster, Anime Girl, Ghost, and more
- 🖥️ **Modern UI** - Built with CustomTkinter

## Installation

```bash
# Clone the repository
git clone https://github.com/luaapy/VoiceChanger.git
cd VoiceChanger

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Requirements

- Python 3.11+
- Windows 10/11 (tested), Linux, macOS
- Audio input device (microphone)
- Audio output device (speakers/headphones)

### Optional: High-Quality Pitch Shifting

For best pitch shifting quality, install rubberband:

**Windows:**
```bash
# Download rubberband from https://breakfastquay.com/rubberband/
# Add the bin folder to your PATH
```

**Linux:**
```bash
sudo apt install rubberband-cli
```

**macOS:**
```bash
brew install rubberband
```

## Presets

| Preset | Description |
|--------|-------------|
| Woman | Female voice (+5 pitch, 1.2 formant) |
| Anime Girl | High-pitched cute voice with chorus |
| Male Voice | Deeper masculine voice |
| Child Voice | High-pitched child voice |
| Monster | Very deep demonic voice |
| Darth Vader | Deep voice with reverb |
| Ghost | Ethereal voice with delay |
| Telephone | Radio/phone effect |

## Usage

1. Launch the application with `python main.py`
2. Select your input device (microphone)
3. Select your output device (speakers or virtual cable)
4. Click **Start** to begin processing
5. Select a preset or adjust sliders manually
6. Speak into your microphone!

## For Streaming/Discord

To use with Discord or other apps:
1. Install [VB-Cable](https://vb-audio.com/Cable/) or similar virtual audio cable
2. Set the voice changer output to the virtual cable
3. In Discord, set your microphone to the virtual cable

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
