import bpy
import re


# ======= CONFIG =======
srt_path = "path to srt file"
#audio_path = "path to audio file"
START_FRAME = 1
# ======================


# parses srt file
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

# convert seconds to frames (assuming 24fps)
def sec_to_frame(sec, fps=24):
    return int(sec * fps)

# create text object and alignes in center
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

# ======= RUN =======
subs = parse_srt(srt_path)
FPS = bpy.context.scene.render.fps
create_lyrics(subs)
print(f"Imported {len(subs)} lyric lines")