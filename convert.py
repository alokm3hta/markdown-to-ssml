import mistune
import sys
import argparse
import html
import os
from typing import Optional, Any
from google.cloud import texttospeech

# Constants
BREAK_TIMES = {1: "300ms", 2: "200ms", 3: "100ms", 4: "0ms"}
PARAGRAPH_BREAK = "100ms"
LINEBREAK = "400ms"
HRULE_BREAK = "600ms"

class SSMLRenderer(mistune.HTMLRenderer):
    def heading(self, text: str, level: int, **kwargs: Any) -> str:
        break_time = BREAK_TIMES.get(level, "0ms")
        return f"{text}<break time=\"{break_time}\"/>\n"

    def emphasis(self, text: str) -> str:
        return f"<emphasis level=\"moderate\">{text}</emphasis>"

    def strong(self, text: str) -> str:
        return f"<emphasis level=\"strong\">{text}</emphasis>"

    def linebreak(self) -> str:
        return f"<break time=\"{LINEBREAK}\"/>\n"

    def thematic_break(self) -> str:
        return f"<break time=\"{HRULE_BREAK}\"/>\n"

    def image(self, src: str, alt: str = "", title: Optional[str] = None) -> str:
        return f"image of {title}" if title else ""

    def paragraph(self, text: str) -> str:
        return f"<p>{text}<break time=\"{PARAGRAPH_BREAK}\"/></p>\n"

    def link(self, text: str, url: str, title: Optional[str] = None) -> str:
        return text

    def text(self, text: str) -> str:
        return html.escape(text)

    def block_code(self, code: str, info: Optional[str] = None) -> str:
        return self.text(code)

    def codespan(self, text: str) -> str:
        return self.text(text)

def markdown_to_ssml(markdown_text: str) -> str:
    renderer = SSMLRenderer()
    markdown = mistune.create_markdown(renderer=renderer)
    out_text = markdown(markdown_text)
    return f"<speak>{out_text}</speak>"

def get_ogg(ssml: str, output_file: str) -> None:
    """
    Get the OGG file from Google Cloud Text-to-Speech API
    """
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

    voice = texttospeech.VoiceSelectionParams(
        language_code='en-US',
        name="en-US-Wavenet-F"
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.OGG_OPUS
    )

    try:
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        with open(output_file, 'wb') as out:
            out.write(response.audio_content)
        print(f'Audio content written to file "{output_file}"')
    except Exception as e:
        print(f"Error generating audio: {e}")

def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to SSML and optionally generate OGG audio.")
    parser.add_argument("input_file", help="Input Markdown file")
    parser.add_argument("--get_ogg", action='store_true', help="Generate OGG audio file")
    args = parser.parse_args()

    # Read input file
    with open(args.input_file, 'r', encoding='utf-8') as f:
        markdown_input = f.read()

    # Generate SSML
    ssml = markdown_to_ssml(markdown_input)

    # Write SSML to file
    ssml_file = os.path.splitext(args.input_file)[0] + '.ssml'
    with open(ssml_file, 'w', encoding='utf-8') as f:
        f.write(ssml)
    print(f"SSML content written to file '{ssml_file}'")

    # Generate OGG if requested
    if args.get_ogg:
        ogg_file = os.path.splitext(args.input_file)[0] + '.ogg'
        get_ogg(ssml, ogg_file)

if __name__ == "__main__":
    main()
