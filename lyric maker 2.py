import bpy
import re
import os

# ======= CONFIG =======
srt_path = "path to srt file"
#audio_path = "path to audio file"
START_FRAME = 1
# ======================

# parses srt file
def parse_srt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    blocks = content.strip().split("\n\n")
    subtitles = []

    for block in blocks:
        lines = block.split("\n")

        if len(lines) >= 3:
            times = re.findall(r"(\d+):(\d+):(\d+),(\d+)", lines[1])
            if len(times) == 2:
                start = (int(times[0][0]) * 3600 + int(times[0][1]) * 60 + int(times[0][2]) + int(times[0][3]) / 1000.0)
                end = (int(times[1][0]) * 3600 + int(times[1][1]) * 60 + int(times[1][2]) + int(times[1][3]) / 1000.0)
                text = "\n".join(lines[2:]).strip()
                subtitles.append((start, end, text))

    # Sort by start time for safety
    subtitles.sort(key=lambda x: x[0])
    return subtitles

'''
this part is not used right now has some bug, just for playing audio inside from blender
so as of now load audio manually or use some external player
def ensure_vse():
    scene = bpy.context.scene
    if scene.sequence_editor is None:
        scene.sequence_editor_create()
    return scene.sequence_editor


def load_audio(filepath, start_frame=START_FRAME, channel=1):
    scene = bpy.context.scene
    seq_ed = ensure_vse()
    filepath = os.path.abspath(filepath)

    # Load sound datablock or reuse if already loaded
    sound = next((s for s in bpy.data.sounds if bpy.path.abspath(s.filepath) == filepath), None)
    if sound is None:
        sound = bpy.data.sounds.load(filepath)

    # Add audio strip
    strip = seq_ed.sequence.new_sound(
        name="Song",
        filepath=filepath,
        channel=channel,
        frame_start=start_frame
    )

    # Determine duration
    duration_frames = getattr(sound, "frame_duration", None)
    if not duration_frames or duration_frames <= 0:
        duration_frames = strip.frame_final_duration

    scene.frame_start = start_frame
    scene.frame_end = start_frame + int(duration_frames)
    return strip
'''

# create text object and alignes in center
def create_text_object():
    bpy.ops.object.text_add(location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = "LyricText"
    obj.data.align_x = 'CENTER'
    obj.data.align_y = 'CENTER'
    obj.data.body = ""

    # Nice font size
    obj.data.size = 1.2
    return obj

# create a material of text object with emmission and transparent shader
def setup_material_for_fade(obj):
    mat = bpy.data.materials.new(name="LyricMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear defaults
    for n in list(nodes):
        nodes.remove(n)

    out = nodes.new("ShaderNodeOutputMaterial")
    mix = nodes.new("ShaderNodeMixShader")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    emission = nodes.new("ShaderNodeEmission")

    emission.inputs["Color"].default_value = (1, 1, 1, 1)
    emission.inputs["Strength"].default_value = 2.0

    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(emission.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs[0])

    obj.data.materials.clear()
    obj.data.materials.append(mat)

    # Eevee transparency settings
    if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
        mat.blend_method = 'BLEND'
        #mat.shadow_method = 'NONE'
    return mat, mix

# adds fades in and fades out animation keyframe
def keyframe_line_fades(mix, subs, fps):
    # Start fully transparent
    mix.inputs[0].default_value = 0.0
    mix.inputs[0].keyframe_insert("default_value", frame=START_FRAME)

    for (start, end, _text) in subs:
        s = int(round(start * fps))
        e = int(round(end * fps))

        # Fade in at start
        mix.inputs[0].default_value = 1.0
        mix.inputs[0].keyframe_insert("default_value", frame=s)

        # Fade out at end
        mix.inputs[0].default_value = 0.0
        mix.inputs[0].keyframe_insert("default_value", frame=e)

# setup frame change handler
def frame_change_handler(scene):
    subtitle = _handler_state["subs"]
    
    obj = bpy.data.objects.get(_handler_state["obj_name"])
    if not obj or not subtitle:
        return

    f = scene.frame_current
    # Find rightmost start <= f
    # Find which subtitle applies
    for (start, end, text) in subtitle:
        s = int(round(start *fps))
        e = int(round(end * fps)) 
        if s <= f <= e:
            if obj.data.body != text:
                obj.data.body = text
            return
        
    # If no subtitle matches, clear text
    if obj.data.body != "":
        obj.data.body = ""

# install frame change handler
def install_handler():
    # Avoid duplicate handlers
    for h in bpy.app.handlers.frame_change_pre:
        if getattr(h, "__name__", "") == "frame_change_handler":
            return
    bpy.app.handlers.frame_change_pre.append(frame_change_handler)

# ======= RUN =======
subs = parse_srt(srt_path)
if not subs:
    raise RuntimeError("No subtitles parsed. Check your SRT path/format.")

#strip = load_audio(audio_path, start_frame=START_FRAME, channel=1)
obj = create_text_object()
mat, mix = setup_material_for_fade(obj)

fps = bpy.context.scene.render.fps
keyframe_line_fades(mix, subs, fps)

# Global storage for handler
_handler_state = {
    "subs": subs,
    "obj_name": obj.name if obj.name else "Lyric Text" ,
}

install_handler()
print(f"Imported {len(subs)} lyric lines")
