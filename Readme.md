# Lyric Video maker in blender - makes lyric video of a song or anything with srt file
1. Lyric Maker 1 - uses only frame change handler (smiple one with no materials)
2. Lyric Maker 2 - uses frame change handler with material's fade in, fade out anination (uses materials)


## Usage

1. Set `srt_path` to your SRT subtitle file path
2. Set `START_FRAME` if needed (default: 1)
3. Run the script in Blender's Scripting workspace
4. Load audio manually or use an external player
5. Play the animation to see lyrics sync with timing

## Features

- Parses SRT subtitle files with precise timing
- Creates centered text object in Blender
- Emissive material with fade in/out animations
- Real-time lyric updates via frame change handler
- Automatic keyframing for transparency

## Requirements

- Blender 2.80+
- SRT subtitle file

## Notes

- Audio playback within Blender is disabled (use external player) or load audio manually
- Material requires Eevee or Cycles renderer
- Lyrics fade in at start time, fade out at end time
