#!/usr/bin/env python3
"""
Wyoming Protocol Server for Vietnamese ASR (Zipformer-30M-RNNT)
Uses wyoming library's AsyncServer pattern for proper protocol handling
"""

import asyncio
import logging
from pathlib import Path

import numpy as np
import sherpa_onnx
from wyoming.audio import AudioStart, AudioChunk, AudioStop
from wyoming.event import Event
from wyoming.info import Describe, Info, Attribution, AsrProgram, AsrModel
from wyoming.server import AsyncEventHandler, AsyncServer
from wyoming.asr import Transcribe, Transcript

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
_LOGGER = logging.getLogger(__name__)

MODEL_DIR = Path("/app/model")
ENCODER_PATH = MODEL_DIR / "encoder-epoch-20-avg-10.onnx"
DECODER_PATH = MODEL_DIR / "decoder-epoch-20-avg-10.onnx"
JOINER_PATH = MODEL_DIR / "joiner-epoch-20-avg-10.onnx"
TOKENS_PATH = MODEL_DIR / "tokens.txt"

recognizer = None


def load_model():
    """Load the Zipformer model"""
    global recognizer
    _LOGGER.info("Loading Vietnamese ASR model...")
    _LOGGER.info(f"Model dir: {MODEL_DIR}")
    _LOGGER.info(f"Files: {list(MODEL_DIR.iterdir())}")
    
    recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=str(ENCODER_PATH),
        decoder=str(DECODER_PATH),
        joiner=str(JOINER_PATH),
        tokens=str(TOKENS_PATH),
        num_threads=4,
        sample_rate=16000,
        provider="cpu",
    )
    _LOGGER.info("Model loaded successfully!")


class VietnameseASREventHandler(AsyncEventHandler):
    """Event handler for Wyoming ASR protocol"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio_buffer = bytearray()
        self.sample_rate = 16000
        self.channels = 1

    async def handle_event(self, event: Event) -> bool:
        """Handle incoming Wyoming events"""
        if Describe.is_type(event.type):
            _LOGGER.info("Handling Describe event")
            info = Info(
                asr=[
                    AsrProgram(
                        name="vietnamese_asr",
                        attribution=Attribution(
                            name="hynth",
                            url="https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h",
                        ),
                        installed=True,
                        description="Vietnamese ASR (Zipformer-30M-RNNT-6000h)",
                        version="1.0.0",
                        models=[
                            AsrModel(
                                name="zipformer-vietnamese-30m",
                                attribution=Attribution(
                                    name="hynth",
                                    url="https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h",
                                ),
                                installed=True,
                                description="Zipformer-30M-RNNT-6000h - WER 7.97% on VLSP2025",
                                version="1.0.0",
                                languages=["vi"],
                            )
                        ],
                    )
                ],
            )
            await self.write_event(info.event())
            return True

        if AudioStart.is_type(event.type):
            audio_start = AudioStart.from_event(event)
            self.sample_rate = audio_start.rate
            self.channels = audio_start.channels
            self.audio_buffer = bytearray()
            _LOGGER.info(f"Audio started: rate={self.sample_rate}, channels={self.channels}")
            return True

        if AudioChunk.is_type(event.type):
            chunk = AudioChunk.from_event(event)
            self.audio_buffer.extend(chunk.audio)
            _LOGGER.debug(f"Audio chunk received: {len(chunk.audio)} bytes")
            return True

        if AudioStop.is_type(event.type):
            _LOGGER.info(f"Audio stopped, buffer size: {len(self.audio_buffer)} bytes")
            
            if len(self.audio_buffer) == 0:
                _LOGGER.warning("Empty audio buffer")
                await self.write_event(Transcript(text="").event())
                return True

            try:
                # Convert bytes to float32 array
                audio_data = np.frombuffer(self.audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Convert multi-channel to mono if needed
                if self.channels > 1:
                    audio_data = audio_data.reshape(-1, self.channels).mean(axis=1)
                
                # Create stream and transcribe
                stream = recognizer.create_stream()
                stream.accept_waveform(self.sample_rate, audio_data)
                recognizer.decode_stream(stream)
                result = stream.result
                
                text = result.text.strip()
                _LOGGER.info(f"Transcription result: '{text}'")
                
                await self.write_event(Transcript(text=text).event())
            except Exception as e:
                _LOGGER.error(f"Error during transcription: {e}", exc_info=True)
                await self.write_event(Transcript(text="").event())
            
            self.audio_buffer = bytearray()
            return True

        if Transcribe.is_type(event.type):
            _LOGGER.info("Transcribe event received (treating as AudioStop)")
            # Handle as if AudioStop
            if len(self.audio_buffer) > 0:
                try:
                    audio_data = np.frombuffer(self.audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
                    if self.channels > 1:
                        audio_data = audio_data.reshape(-1, self.channels).mean(axis=1)
                    
                    stream = recognizer.create_stream()
                    stream.accept_waveform(self.sample_rate, audio_data)
                    recognizer.decode_stream(stream)
                    result = stream.result
                    
                    text = result.text.strip()
                    _LOGGER.info(f"Transcription result: '{text}'")
                    await self.write_event(Transcript(text=text).event())
                except Exception as e:
                    _LOGGER.error(f"Error during transcription: {e}", exc_info=True)
                    await self.write_event(Transcript(text="").event())
                finally:
                    self.audio_buffer = bytearray()
            return True

        _LOGGER.debug(f"Unhandled event type: {event.type}")
        return True


def handler_factory(reader, writer):
    """Factory function to create event handlers"""
    return VietnameseASREventHandler(reader, writer)


async def main():
    """Main entry point"""
    _LOGGER.info("Starting Wyoming Vietnamese ASR Server")
    
    load_model()
    
    server = AsyncServer.from_uri("tcp://0.0.0.0:10400")
    _LOGGER.info("Wyoming server listening on 0.0.0.0:10400")
    
    await server.run(handler_factory)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("Server stopped by user")
    except Exception as e:
        _LOGGER.error(f"Server error: {e}", exc_info=True)
