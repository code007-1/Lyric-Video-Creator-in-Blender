import os
import bpy
import re

# ======= CONFIG =======
srt_path = "D:/Songs/blender files/League of Legends - Legends Never Die.en.srt"
audio_path = "D:/Songs/blender files/legends never die.mp3"
FPS = bpy.context.scene.render.fps  # use scene FPS
START_FRAME = 1
# ======================

# Path to your SRT file


# Function to parse SRT file
def parse_srt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split blocks by double newlines
    blocks = content.strip().split("\n\n")
    subtitles = []
    for block in blocks:
        lines = block.split("\n")
        if len(lines) >= 3:
            # Extract time range
            times = re.findall(r"(\d+):(\d+):(\d+),(\d+)", lines[1])
            if len(times) == 2:
                start = int(times[0][0])*3600 + int(times[0][1])*60 + int(times[0][2]) + int(times[0][3])/1000
                end   = int(times[1][0])*3600 + int(times[1][1])*60 + int(times[1][2]) + int(times[1][3])/1000
                text  = "\n".join(lines[2:])
                subtitles.append((start, end, text))
    return subtitles

# Convert seconds to frames (assuming 24fps)
def sec_to_frame(sec, fps=24):
    return int(sec * fps)

# create a sequqnce editor if not created already
def ensure_vse():
    scene = bpy.context.scene
    if scene.sequence_editor is None:
        scene.sequence_editor_create()
    return scene.sequence_editor

# Create text objects with keyframes
def create_lyrics(subtitles):
    # If using Eevee, set material blend mode for proper transparency
    use_eevee = (bpy.context.scene.render.engine == 'BLENDER_EEVEE')
    for i, (start, end, text) in enumerate(subtitles):
        bpy.ops.object.text_add(location=(0, 0, i * -0.5))
        obj = bpy.context.object
        obj.data.body = text
        obj.data.align_x = 'CENTER'
        obj.data.align_y = 'CENTER'

        # Create transparent+emission material
        mat = bpy.data.materials.new(name=f"LyricMat_{i}")
        mat.use_nodes = True
        nt = mat.node_tree
        nodes = nt.nodes
        links = nt.links

        # Clear default nodes to avoid naming ambiguity
        for n in list(nodes):
            nodes.remove(n)

        out = nodes.new("ShaderNodeOutputMaterial")
        mix = nodes.new("ShaderNodeMixShader")
        transparent = nodes.new("ShaderNodeBsdfTransparent")
        emission = nodes.new("ShaderNodeEmission")

        # Style: white emission; tweak strength for glow
        emission.inputs["Color"].default_value = (1, 1, 1, 1)
        emission.inputs["Strength"].default_value = 2.0

        links.new(transparent.outputs[0], mix.inputs[1])
        links.new(emission.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], out.inputs[0])

        obj.data.materials.append(mat)

        # Eevee transparency settings
        if use_eevee:
            mat.blend_method = 'BLEND'
            #mat.shadow_method = 'NONE'

        # Start invisible well before any text start
        first_frame = max(START_FRAME, 1)
        mix.inputs[0].default_value = 0.0
        mix.inputs[0].keyframe_insert("default_value", frame=first_frame)

        # Fade in at start time (instant or small ramp)
        start_f = sec_to_frame(start)
        mix.inputs[0].default_value = 1.0
        mix.inputs[0].keyframe_insert("default_value", frame=start_f)

        # Fade out at end time
        end_f = sec_to_frame(end)
        mix.inputs[0].default_value = 0.0
        mix.inputs[0].keyframe_insert("default_value", frame=end_f)

        # Optional: also keyframe object visibility to be safe in viewport/render
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=first_frame)
        obj.keyframe_insert(data_path="hide_render", frame=first_frame)

        obj.hide_viewport = False
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_viewport", frame=start_f)
        obj.keyframe_insert(data_path="hide_render", frame=start_f)

        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=end_f)
        obj.keyframe_insert(data_path="hide_render", frame=end_f)

'''# Load audio into VSE
def load_audio(filepath, start_frame=START_FRAME, channel=1):
    scene = bpy.context.scene
    seq_ed = ensure_vse()
    
    # Ensure absolute path
    filepath = os.path.abspath(filepath)
    
    # Load sound datablock (avoid duplicates)
    sound = None
    for s in bpy.data.sounds:
        if bpy.path.abspath(s.filepath) == filepath:
            sound = s
            break
    
    if sound is None:
        sound = bpy.data.sounds.load(filepath)

    # Add audio strip using the data API
    strip = seq_ed.sequences.new_sound(
        name="Song",
        filepath=filepath,
        channel=channel,
        frame_start=start_frame
    )

    # Set timeline end to cover the audio duration
    # Some Blender versions compute duration via sound.frame_duration; otherwise use strip.frame_final_duration
    duration_frames = getattr(sound, "frame_duration", None)
    if duration_frames is None or duration_frames <= 0:
        duration_frames = strip.frame_final_duration

    scene.frame_start = start_frame
    scene.frame_end = start_frame + int(duration_frames)

    return strip'''

# ======= RUN =======
subs = parse_srt(srt_path)
#load_audio(audio_path, start_frame=START_FRAME, channel=1)
create_lyrics(subs)
print(f"Imported {len(subs)} lyric lines and loaded audio.")